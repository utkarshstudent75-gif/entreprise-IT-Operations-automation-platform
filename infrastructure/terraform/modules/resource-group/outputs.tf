# Outputs for the module will be defined here as resources are implemented.
output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.this.name
}

output "resource_group_id" {
  description = "The ID of the resource group"
  value       = azurerm_resource_group.this.id
}

output "location" {
  description = "The azure region of the resource group"
  value       = azurerm_resource_group.this.location
}