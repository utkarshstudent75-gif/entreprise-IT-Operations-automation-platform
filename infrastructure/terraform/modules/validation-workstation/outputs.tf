output "vm_id" {
  description = "The ID of the Windows Virtual Machine."
  value       = azurerm_windows_virtual_machine.this.id
}

output "vm_name" {
  description = "The name of the Windows Virtual Machine."
  value       = azurerm_windows_virtual_machine.this.name
}

output "public_ip" {
  description = "The public IP address of the workstation (if enabled)."
  value       = var.enable_public_ip && length(azurerm_public_ip.this) > 0 ? azurerm_public_ip.this[0].ip_address : null
}

output "private_ip" {
  description = "The private IP address of the workstation."
  value       = azurerm_network_interface.this.ip_configuration[0].private_ip_address
}

output "managed_identity_principal_id" {
  description = "The principal ID of the System-Assigned Managed Identity for the VM."
  value       = azurerm_windows_virtual_machine.this.identity[0].principal_id
}
