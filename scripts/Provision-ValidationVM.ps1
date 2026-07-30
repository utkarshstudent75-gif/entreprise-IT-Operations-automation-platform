# Provision-ValidationVM.ps1
# Automates the Terraform provisioning of the EITOAP Validation Workstation

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TfDir = Join-Path $ScriptDir "../infrastructure/terraform/environments/dev"

Write-Output "=== EITOAP Validation VM Provisioner ==="
Write-Output "Target Terraform directory: $TfDir"

Push-Location $TfDir

try {
    Write-Output "Running 'terraform init'..."
    terraform init
    if ($LASTEXITCODE -ne 0) { throw "Terraform init failed." }

    Write-Output "Running 'terraform apply'..."
    terraform apply -auto-approve
    if ($LASTEXITCODE -ne 0) { throw "Terraform apply failed." }

    Write-Output "Fetching VM outputs..."
    $vmName = terraform output -raw -json | convertfrom-json | select-object -expandproperty validation_workstation_name -ErrorAction SilentlyContinue
    $publicIp = terraform output -raw -json | convertfrom-json | select-object -expandproperty validation_workstation_public_ip -ErrorAction SilentlyContinue
    $privateIp = terraform output -raw -json | convertfrom-json | select-object -expandproperty validation_workstation_private_ip -ErrorAction SilentlyContinue

    Write-Output "--------------------------------------------------"
    Write-Output "Validation Workstation Provisioned Successfully!"
    Write-Output "VM Name:    $vmName"
    Write-Output "Public IP:  $publicIp"
    Write-Output "Private IP: $privateIp"
    Write-Output "--------------------------------------------------"
    Write-Output "To retrieve the local admin password, run:"
    Write-Output "az keyvault secret show --name validation-vm-admin-password --vault-name <your-keyvault-name> --query value -o tsv"
    Write-Output "--------------------------------------------------"
}
catch {
    Write-Error "Error during VM provisioning: $_"
    Pop-Location
    exit 1
}

Pop-Location
exit 0
