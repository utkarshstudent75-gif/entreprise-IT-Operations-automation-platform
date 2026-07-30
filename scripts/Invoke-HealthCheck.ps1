# Invoke-HealthCheck.ps1
# Performs automated platform checks, local workstation verification, and infrastructure validation.

param(
    [string]$ResourceGroupName = "eitoap-dev-rg",
    [string]$AksClusterName = "enterprise-dev-aks",
    [string]$DashboardUrl = "http://portal.company.com/dashboard",
    [string]$TargetTimezone = "Eastern Standard Time"
)

Write-Output "========================================================="
Write-Output "  Enterprise IT Operations Platform - Health Check Script "
Write-Output "========================================================="

$passCount = 0
$failCount = 0

function Report-Check {
    param(
        [string]$Name,
        [bool]$Success,
        [string]$Details = ""
    )
    if ($Success) {
        Write-Host -ForegroundColor Green "[ PASS ] $Name ($Details)"
        $script:passCount++
    } else {
        Write-Host -ForegroundColor Red "[ FAIL ] $Name ($Details)"
        $script:failCount++
    }
}

# --- 1. LOCAL WORKSTATION VERIFICATION ---
Write-Output "`n1. Verifying Local OS Settings & Registry Policies..."

# Check RDP Registry configuration
$rdpDeny = Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -ErrorAction SilentlyContinue
if ($rdpDeny -and $rdpDeny.fDenyTSConnections -eq 0) {
    Report-Check "Remote Desktop Enabled" $true "Registry fDenyTSConnections set to 0"
} else {
    Report-Check "Remote Desktop Enabled" $false "Registry key missing or disabled"
}

# Check Timezone configuration
$tz = Get-TimeZone
if ($tz.Id -eq $TargetTimezone) {
    Report-Check "Timezone Alignment" $true "Matches target '$TargetTimezone'"
} else {
    Report-Check "Timezone Alignment" $false "Current: '$($tz.Id)', expected: '$TargetTimezone'"
}

# Check Chocolatey Installed
if (Get-Command choco -ErrorAction SilentlyContinue) {
    Report-Check "Chocolatey Installation" $true "Choco tool exists"
    
    # Check git, vscode, azure-cli
    $gitExists = [bool](Get-Command git -ErrorAction SilentlyContinue)
    $codeExists = [bool](Get-Command code -ErrorAction SilentlyContinue)
    $azExists = [bool](Get-Command az -ErrorAction SilentlyContinue)
    
    Report-Check "Git CLI" $gitExists ($gitExists ? "Found" : "Not found")
    Report-Check "VS Code CLI" $codeExists ($codeExists ? "Found" : "Not found")
    Report-Check "Azure CLI" $azExists ($azExists ? "Found" : "Not found")
} else {
    Report-Check "Chocolatey Installation" $false "Chocolatey is not installed"
}

# Check Startup Script Launch File
$startupPath = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\launch-edge.cmd"
if (Test-Path $startupPath) {
    $content = Get-Content $startupPath
    if ($content -like "*$DashboardUrl*") {
        Report-Check "Edge Auto-Startup Shortcut" $true "Configured for $DashboardUrl"
    } else {
        Report-Check "Edge Auto-Startup Shortcut" $false "Incorrect dashboard URL in launch file"
    }
} else {
    Report-Check "Edge Auto-Startup Shortcut" $false "Startup batch file missing"
}

# --- 2. REMOTE PLATFORM INFRASTRUCTURE CHECKS ---
Write-Output "`n2. Verifying Azure & Kubernetes platform components..."

# Check if az CLI is signed in (optional, only runs if logged in)
if (Get-Command az -ErrorAction SilentlyContinue) {
    $azAccount = az account show -o json | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($azAccount) {
        Report-Check "Azure Session Authentication" $true "Active Tenant: $($azAccount.tenantId)"
        
        # Check Resource Group
        $rg = az group show --name $ResourceGroupName -o json | ConvertFrom-Json -ErrorAction SilentlyContinue
        Report-Check "Azure Resource Group ($ResourceGroupName)" ($null -ne $rg) ($null -ne $rg ? "Active" : "Not found")
        
        # Check AKS Cluster status
        $aks = az aks show --resource-group $ResourceGroupName --name $AksClusterName -o json | ConvertFrom-Json -ErrorAction SilentlyContinue
        Report-Check "AKS Cluster ($AksClusterName)" ($null -ne $aks) ($null -ne $aks ? "ProvisioningState: $($aks.provisioningState)" : "Not found")
    } else {
        Write-Warning "Azure CLI is installed but not authenticated. Skipping Azure environment validations..."
    }
} else {
    Write-Warning "Azure CLI is missing. Skipping Azure environment validations..."
}

# Check Kubernetes endpoint health (via kubectl if active)
if (Get-Command kubectl -ErrorAction SilentlyContinue) {
    $clusterInfo = kubectl cluster-info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Report-Check "Kubernetes API Connection" $true "Connects to server"
        
        # Pods checks in backend & frontend
        $backendPods = kubectl get pods -n backend -o json | ConvertFrom-Json -ErrorAction SilentlyContinue
        $backendOk = [bool]($backendPods -and $backendPods.items -and ($backendPods.items | Where-Object { $_.status.phase -eq "Running" }))
        Report-Check "Kubernetes Backend Pods" $backendOk ($backendOk ? "Healthy" : "Failed or not deployed")

        $frontendPods = kubectl get pods -n frontend -o json | ConvertFrom-Json -ErrorAction SilentlyContinue
        $frontendOk = [bool]($frontendPods -and $frontendPods.items -and ($frontendPods.items | Where-Object { $_.status.phase -eq "Running" }))
        Report-Check "Kubernetes Frontend Pods" $frontendOk ($frontendOk ? "Healthy" : "Failed or not deployed")
    } else {
        Write-Warning "Kubernetes cluster connection is unavailable. Skipping pod checks..."
    }
}

# Check Application API health (PostgreSQL & Redis)
try {
    Write-Output "Testing API Readiness endpoint..."
    $response = Invoke-RestMethod -Uri "$DashboardUrl/api/v1/readiness" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response -and $response.status -eq "ready") {
        Report-Check "Application Central API (/api/v1/readiness)" $true "Ready"
        Report-Check "PostgreSQL Connection via API" ($response.database -eq "connected") ($response.database -eq "connected" ? "Connected" : "Offline")
        Report-Check "Redis Cache Connection via API" ($response.redis -eq "connected") ($response.redis -eq "connected" ? "Connected" : "Offline")
    } else {
        Report-Check "Application Central API (/api/v1/readiness)" $false "Response: $response"
    }
} catch {
    # If the local dashboard mapping isn't fully set up yet, this will fail. That's expected in isolated tests.
    Report-Check "Application Central API (/api/v1/readiness)" $false "Endpoint unreachable: $($_.Exception.Message)"
}

Write-Output "`n========================================================="
Write-Output "Verification Summary:"
Write-Output "  Passed Checks: $passCount"
if ($failCount -gt 0) {
    Write-Host -ForegroundColor Red "  Failed Checks: $failCount"
    Write-Host -ForegroundColor Red "HEALTH STATUS: FAIL"
    exit 1
} else {
    Write-Host -ForegroundColor Green "HEALTH STATUS: PASS"
    exit 0
}
