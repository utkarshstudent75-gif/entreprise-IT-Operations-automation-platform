# Validation Workstation Infrastructure Module

# 1. Public IP Address (Optional)
resource "azurerm_public_ip" "this" {
  count               = var.enable_public_ip ? 1 : 0
  name                = "${var.vm_name}-pip"
  resource_group_name = var.resource_group_name
  location            = var.location
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

# 2. Network Security Group (NSG) and Rules
resource "azurerm_network_security_group" "this" {
  name                = "${var.vm_name}-nsg"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  # Allow outbound internet for Azure AD Join, App downloads, etc.
  security_rule {
    name                       = "allow-outbound-internet"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  # Restrict inbound RDP to specified source ranges
  security_rule {
    name                       = "allow-inbound-rdp"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefixes    = var.allowed_inbound_rdp_ips
    destination_address_prefix = "*"
  }
}

# 3. Network Interface Card (NIC)
resource "azurerm_network_interface" "this" {
  name                = "${var.vm_name}-nic"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = var.enable_public_ip ? azurerm_public_ip.this[0].id : null
  }
}

# 4. Associate NSG to NIC
resource "azurerm_network_interface_security_group_association" "this" {
  network_interface_id      = azurerm_network_interface.this.id
  network_security_group_id = azurerm_network_security_group.this.id
}

# 5. Windows 11 Virtual Machine (Trusted Launch Enabled)
resource "azurerm_windows_virtual_machine" "this" {
  name                = var.vm_name
  resource_group_name = var.resource_group_name
  location            = var.location
  size                = "Standard_D2s_v5"
  admin_username      = var.admin_username
  admin_password      = var.admin_password
  network_interface_ids = [
    azurerm_network_interface.this.id,
  ]

  source_image_reference {
    publisher = "MicrosoftWindowsDesktop"
    offer     = "windows-11"
    sku       = "win11-23h2-ent"
    version   = "latest"
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 128
  }

  # Managed identity is mandatory for AMA and Microsoft Entra Join
  identity {
    type = "SystemAssigned"
  }

  # Trusted Launch configurations
  secure_boot_enabled = true
  vtpm_enabled        = true

  # Managed boot diagnostics (zero-cost, no storage account required)
  boot_diagnostics {}

  tags = var.tags
}

# 6. Auto Shutdown Schedule (7:00 PM Eastern standard Time)
resource "azurerm_dev_test_global_vm_shutdown_schedule" "this" {
  virtual_machine_id = azurerm_windows_virtual_machine.this.id
  location           = var.location
  enabled            = true

  daily_recurrence_time = "1900"
  timezone              = "Eastern Standard Time"

  notification_settings {
    enabled = false
  }
}

# 7. Microsoft Entra Join VM Extension (AADLoginForWindows)
resource "azurerm_virtual_machine_extension" "aad_login" {
  name                       = "AADLoginForWindows"
  virtual_machine_id         = azurerm_windows_virtual_machine.this.id
  publisher                  = "Microsoft.Azure.ActiveDirectory"
  type                       = "AADLoginForWindows"
  type_handler_version       = "2.2"
  auto_upgrade_minor_version = true
  tags                       = var.tags
}

# 8. Azure Monitor Agent (AMA) VM Extension
resource "azurerm_virtual_machine_extension" "azure_monitor" {
  name                       = "AzureMonitorWindowsAgent"
  virtual_machine_id         = azurerm_windows_virtual_machine.this.id
  publisher                  = "Microsoft.Azure.Monitor"
  type                       = "AzureMonitorWindowsAgent"
  type_handler_version       = "1.22"
  auto_upgrade_minor_version = true
  automatic_upgrade_enabled  = true
  tags                       = var.tags
}

# 9. Custom Script Extension to execute workstation configuration
resource "azurerm_virtual_machine_extension" "custom_script" {
  name                 = "CustomScriptExtension"
  virtual_machine_id   = azurerm_windows_virtual_machine.this.id
  publisher            = "Microsoft.Compute"
  type                 = "CustomScriptExtension"
  type_handler_version = "1.10"
  tags                 = var.tags

  settings = jsonencode({
    commandToExecute = "powershell -ExecutionPolicy Bypass -Command \"[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('${base64encode(var.startup_script_content)}')) | Out-File -FilePath C:\\configure.ps1; powershell -ExecutionPolicy Bypass -File C:\\configure.ps1\""
  })

  depends_on = [
    azurerm_virtual_machine_extension.aad_login
  ]
}
