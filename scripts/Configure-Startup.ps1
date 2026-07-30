# Configure-Startup.ps1
# Configures Edge to launch automatically upon Windows user login.
# Must be executed in an Elevated PowerShell Session on the VM.

param(
    [string]$DashboardUrl = "http://portal.company.com/dashboard"
)

Write-Output "=== EITOAP Workstation Automatic Browser Launch Configurator ==="

$startupFolder = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"

if (-not (Test-Path $startupFolder)) {
    Write-Output "Creating Startup folder directory: $startupFolder"
    New-Item -ItemType Directory -Force -Path $startupFolder | Out-Null
}

$cmdPath = Join-Path $startupFolder "launch-edge.cmd"
Write-Output "Writing startup launch command to: $cmdPath"

$cmdContent = "start msedge.exe `"$DashboardUrl`""
$cmdContent | Out-File -FilePath $cmdPath -Encoding ASCII -Force

Write-Output "Automatic startup launch configured successfully!"
exit 0
