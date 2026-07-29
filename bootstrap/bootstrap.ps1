# ==============================================================================
# Enterprise IT Operations Platform - Azure Bootstrap (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

# Helper logging functions
function Log-Info ($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Log-Warn ($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Log-Error ($Message) {
    Write-Error "[ERROR] $Message"
}

function Log-Success ($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Confirm-Action ($Prompt) {
    $choice = Read-Host "$Prompt [y/N]"
    return ($choice -like "y*" -or $choice -like "Y*")
}

function Verify-Tool ($Name, $Guidance) {
    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        Log-Info "Verified dependency: $Name"
        return $true
    } else {
        Log-Warn "Missing required dependency: $Name"
        Write-Host "  To install: $Guidance"
        return $false
    }
}

Log-Success "========================================================="
Log-Success "  Enterprise IT Operations Platform - Azure Bootstrap  "
Log-Success "========================================================="

# ------------------------------------------------------------------------------
# 1. Dependency Checks
# ------------------------------------------------------------------------------
Log-Info "1. Verifying pre-requisites and CLI dependencies..."
$hasMissingDeps = $false

if (-not (Verify-Tool "az" "Install Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "terraform" "Install Terraform: https://developer.hashicorp.com/terraform/downloads")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "kubectl" "Install kubectl: https://kubernetes.io/docs/tasks/tools/")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "helm" "Install Helm: https://helm.sh/docs/intro/install/")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "docker" "Install Docker: https://docs.docker.com/engine/install/")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "git" "Install Git: https://git-scm.com/downloads")) { $hasMissingDeps = $true }
if (-not (Verify-Tool "jq" "Install jq: choco install jq (Windows) or brew install jq (macOS)")) { $hasMissingDeps = $true }

if ($hasMissingDeps) {
    Log-Error "Missing required dependencies. Please install them and try again."
    exit 1
}

# Load environment defaults if .env exists
$projectName = "eitoap"
$location = "eastus"
$environment = "dev"
$backendRg = "eitoap-tfstate-rg"
$backendStoragePrefix = "eitoaptfstate"
$backendContainer = "tfstate"
$spName = "eitoap-github"

$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Log-Info "Loading settings from .env..."
    Get-Content $envFile | Where-Object { $_ -match "^[^#].*=" } | ForEach-Object {
        $parts = $_ -split '=', 2
        $key = $parts[0].Trim()
        $val = $parts[1].Trim().Trim('"').Trim("'")
        switch ($key) {
            "EITOAP_PROJECT_NAME" { $projectName = $val }
            "EITOAP_LOCATION" { $location = $val }
            "EITOAP_ENVIRONMENT" { $environment = $val }
            "EITOAP_BACKEND_RG" { $backendRg = $val }
            "EITOAP_BACKEND_STORAGE" { $backendStoragePrefix = $val }
            "EITOAP_BACKEND_CONTAINER" { $backendContainer = $val }
            "EITOAP_SP_NAME" { $spName = $val }
        }
    }
}

# ------------------------------------------------------------------------------
# 2. Azure Authentication & Subscription Selection
# ------------------------------------------------------------------------------
Log-Info "2. Verifying Azure Authentication..."

$authTest = az account show 2>$null
if (-not $authTest) {
    Log-Warn "Not logged into Azure. Initiating 'az login'..."
    az login --use-device-code
}

$subsJson = az account list -o json | ConvertFrom-Json
$subCount = $subsJson.Count

if ($subCount -eq 0) {
    Log-Error "No Azure subscriptions found for the current login session."
    exit 1
}

$selectedSubId = ""
if ($subCount -gt 1) {
    Log-Warn "Multiple Azure subscriptions detected ($subCount):"
    for ($i = 0; $i -lt $subCount; $i++) {
        $defaultStr = if ($subsJson[$i].isDefault) { " (Default)" } else { "" }
        Write-Host "$($i + 1)) $($subsJson[$i].name) ($($subsJson[$i].id))$defaultStr"
    }
    
    $subChoice = Read-Host "Select a subscription index (1-$subCount) [Press Enter for default]"
    if ([string]::IsNullOrWhiteSpace($subChoice)) {
        $selectedSubId = (az account show --query id -o tsv).Trim()
    } else {
        $idx = [int]$subChoice - 1
        $selectedSubId = $subsJson[$idx].id
        Log-Info "Setting active subscription..."
        az account set --subscription $selectedSubId
    }
} else {
    $selectedSubId = $subsJson[0].id
    az account set --subscription $selectedSubId
}

$currentSubName = (az account show --query name -o tsv).Trim()
$tenantId = (az account show --query tenantId -o tsv).Trim()
$currentUser = (az account show --query user.name -o tsv).Trim()

Log-Success "Active Azure Session Details:"
Write-Host "  User:         $currentUser"
Write-Host "  Tenant ID:    $tenantId"
Write-Host "  Subscription: $currentSubName ($selectedSubId)"

if (-not (Confirm-Action "Do you want to continue with this subscription?")) {
    Log-Info "Bootstrap cancelled by user."
    exit 0
}

# ------------------------------------------------------------------------------
# 3. Create/Verify Terraform Backend (Storage Account)
# ------------------------------------------------------------------------------
Log-Info "3. Preparing Terraform state backend..."

$rgTest = az group show --name $backendRg 2>$null
if (-not $rgTest) {
    Log-Info "Creating backend Resource Group '$backendRg' in $location..."
    az group create --name $backendRg --location $location | Out-Null
}

$storageAccountName = $backendStoragePrefix.ToLower() -replace '[^a-z0-9]', ''
if ($storageAccountName.Length -gt 24) { $storageAccountName = $storageAccountName.Substring(0, 24) }

while ($true) {
    $availJson = az storage account check-name --name $storageAccountName -o json | ConvertFrom-Json
    if ($availJson.nameAvailable) {
        break
    }
    
    # Check if exists in our RG
    $exists = az storage account list --resource-group $backendRg --query "[?name=='$storageAccountName'] | length(@)" -o tsv 2>$null
    if ($exists -and [int]$exists -gt 0) {
        break
    }
    
    $suffix = Get-Random -Minimum 10000 -Maximum 99999
    $storageAccountName = ($backendStoragePrefix.Substring(0, [System.Math]::Min(18, $backendStoragePrefix.Length)) + $suffix).ToLower() -replace '[^a-z0-9]', ''
}

Log-Info "Using Storage Account: '$storageAccountName'"

$exists = az storage account list --resource-group $backendRg --query "[?name=='$storageAccountName'] | length(@)" -o tsv 2>$null
if (-not $exists -or [int]$exists -eq 0) {
    Log-Info "Creating Storage Account '$storageAccountName'..."
    az storage account create `
        --name $storageAccountName `
        --resource-group $backendRg `
        --location $location `
        --sku Standard_LRS `
        --kind StorageV2 `
        --encryption-services blob | Out-Null
}

$accountKey = (az storage account keys list --resource-group $backendRg --account-name $storageAccountName --query '[0].value' -o tsv).Trim()

$containerExists = az storage container exists --name $backendContainer --account-name $storageAccountName --account-key $accountKey --query "exists" -o tsv
if ($containerExists -eq "false") {
    Log-Info "Creating blob container '$backendContainer'..."
    az storage container create --name $backendContainer --account-name $storageAccountName --account-key $accountKey | Out-Null
}

Log-Success "Terraform backend storage verification complete!"

# ------------------------------------------------------------------------------
# 4. Create/Verify Service Principal
# ------------------------------------------------------------------------------
Log-Info "4. Configuring Service Principal for GitHub Actions..."
$spAppId = ""
$spClientSecret = ""

$existingApp = az ad app list --display-name $spName -o json | ConvertFrom-Json
if ($existingApp.Count -gt 0) {
    Log-Info "Found existing Application registration: '$spName'"
    $spAppId = $existingApp[0].appId
    
    if (Confirm-Action "Service Principal exists. Do you want to reset its client secret?") {
        Log-Info "Resetting Service Principal credentials..."
        $resetJson = az ad sp credential reset --id $spAppId -o json | ConvertFrom-Json
        $spClientSecret = $resetJson.password
    }
} else {
    Log-Info "Creating a new Service Principal: '$spName'..."
    $spJson = az ad sp create-for-rbac `
        --name $spName `
        --role Contributor `
        --scopes "/subscriptions/$selectedSubId" `
        --json-auth | ConvertFrom-Json
        
    $spAppId = $spJson.clientId
    $spClientSecret = $spJson.clientSecret
}

Log-Success "Service Principal Configured:"
Write-Host "  Client ID: $spAppId"
Write-Host "  Tenant ID: $tenantId"

$bootstrapOutput = Join-Path $PSScriptRoot ".bootstrap-output.json"
$outputObj = @{
    AZURE_CLIENT_ID = $spAppId
    AZURE_CLIENT_SECRET = $spClientSecret
    AZURE_SUBSCRIPTION_ID = $selectedSubId
    AZURE_TENANT_ID = $tenantId
    TF_BACKEND_RG = $backendRg
    TF_BACKEND_STORAGE = $storageAccountName
    TF_BACKEND_CONTAINER = $backendContainer
}
$outputObj | ConvertTo-Json | Out-File $bootstrapOutput -Encoding utf8
Log-Info "Secrets written securely to local metadata: $bootstrapOutput"

# ------------------------------------------------------------------------------
# 5. GitHub Secrets Integration
# ------------------------------------------------------------------------------
Log-Info "5. Configuring GitHub Secrets..."
$secretsTxt = Join-Path $PSScriptRoot "github-secrets.txt"
$secretsContent = @"
===================================================================
GitHub Secrets Configuration (Manual Copy Required)
===================================================================
AZURE_CLIENT_ID=$spAppId
AZURE_CLIENT_SECRET=$spClientSecret
AZURE_SUBSCRIPTION_ID=$selectedSubId
AZURE_TENANT_ID=$tenantId
"@

$secretsContent | Out-File $secretsTxt -Encoding utf8
Log-Success "Secrets file written to $secretsTxt."

# ------------------------------------------------------------------------------
# 6. Terraform Execution
# ------------------------------------------------------------------------------
Log-Info "6. Starting Terraform initialization..."
$tfEnvDir = Join-Path $PSScriptRoot "../infrastructure/terraform/environments/$environment"

if (-not (Test-Path $tfEnvDir)) {
    Log-Error "Terraform environment folder '$tfEnvDir' not found."
    exit 1
}

Push-Location $tfEnvDir
try {
    terraform init `
        -backend-config="resource_group_name=$backendRg" `
        -backend-config="storage_account_name=$storageAccountName" `
        -backend-config="container_name=$backendContainer" `
        -backend-config="key=$environment.terraform.tfstate" `
        -reconfigure
        
    terraform validate
    terraform plan -out=tfplan
    
    if (Confirm-Action "Do you want to apply this Terraform plan?") {
        terraform apply tfplan
        
        $acrName = (terraform output -raw acr_name 2>$null)
        $aksClusterName = (terraform output -raw aks_cluster_name 2>$null)
        $activeRg = "$projectName-$environment-rg"
        
        Log-Info "Retrieving AKS Kubernetes credentials..."
        az aks get-credentials --resource-group $activeRg --name $aksClusterName --overwrite-existing
        
        Log-Info "Verifying cluster health..."
        kubectl get nodes
    }
} finally {
    Pop-Location
}

Log-Success "========================================================="
Log-Success "Bootstrap Script Completed Successfully!"
Log-Success "========================================================="
