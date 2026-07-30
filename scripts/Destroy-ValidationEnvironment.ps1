# Destroy-ValidationEnvironment.ps1
# Automates the Terraform teardown of the EITOAP Validation Workstation

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TfDir = Join-Path $ScriptDir "../infrastructure/terraform/environments/dev"

Write-Output "=== EITOAP Validation VM Destroyer ==="
Write-Output "Target Terraform directory: $TfDir"

Push-Location $TfDir

try {
    # Note: Since the validation workstation resides inside the main Terraform environment state, 
    # we target ONLY the validation workstation modules to avoid tearing down the core infrastructure!
    # This prevents breaking the PostgreSQL, Redis, ACR, and AKS resources.
    Write-Output "Destroying only the validation workstation modules to protect core infrastructure..."
    
    terraform destroy -target=module.validation_workstation -target=module.vm_identity_assignment -target=module.startup_script -target=random_password.vm_admin_password -target=azurerm_key_vault_secret.vm_admin_password -auto-approve
    
    if ($LASTEXITCODE -ne 0) {
        throw "Terraform targeted destroy failed."
    }

    Write-Output "--------------------------------------------------"
    Write-Output "Validation Workstation Destroyed Successfully!"
    Write-Output "--------------------------------------------------"
}
catch {
    Write-Error "Error during VM destruction: $_"
    Pop-Location
    exit 1
}

Pop-Location
exit 0
