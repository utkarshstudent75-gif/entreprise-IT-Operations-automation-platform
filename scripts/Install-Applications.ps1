# Install-Applications.ps1
# Automates application installation on the Windows VM using Chocolatey.
# Must be executed in an Elevated PowerShell Session on the VM.

Write-Output "=== EITOAP Workstation Application Installer ==="

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as an Administrator."
    exit 1
}

# Install Chocolatey if not present
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Output "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    $installScript = (New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')
    Invoke-Expression $installScript
}

# Refresh path variables for the current environment block
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# List of applications to install
$apps = @("git", "vscode", "powershell-core", "azure-cli")

foreach ($app in $apps) {
    Write-Output "Checking package: $app..."
    choco install $app -y --no-progress --limit-output
}

Write-Output "Application installations complete!"
exit 0
