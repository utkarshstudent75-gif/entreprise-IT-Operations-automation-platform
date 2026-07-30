# Configure-VM.ps1
# Configures Windows system services, firewall rules, timezone, RDP, and updates.
# Must be executed in an Elevated PowerShell Session on the VM.

Write-Output "=== EITOAP Workstation Operating System Configurator ==="

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "This script must be run as an Administrator. Please restart PowerShell with administrative privileges."
    exit 1
}

# 1. Enable RDP (NLA disabled for Linux RDP Client compatibility)
Write-Output "Enabling Remote Desktop Services..."
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0 -Force
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name "UserAuthentication" -Value 0 -Force
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# 2. Enable Clipboard Redirection
Write-Output "Enabling Clipboard sharing..."
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' -Name "DisableClipRedir" -Value 0 -ErrorAction SilentlyContinue

# 3. Configure Time Synchronization
Write-Output "Configuring W32Time service and Windows Time Synchronization..."
Set-Service -Name W32Time -StartupType Automatic
Start-Service -Name W32Time -ErrorAction SilentlyContinue
w32tm /config /manualpeerlist:"time.windows.com,0x1" /syncfromflags:manual /reliable:YES /update
w32tm /resync /force

# 4. Enable Automatic Windows Updates
Write-Output "Configuring Automatic Windows Updates..."
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update' -Name "AUOptions" -Value 4 -Force

Write-Output "OS configuration complete!"
exit 0
