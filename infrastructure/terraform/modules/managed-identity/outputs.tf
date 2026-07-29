output "identity_id" {
  description = "The ID of the user assigned managed identity."
  value       = azurerm_user_assigned_identity.this.id
}

output "identity_name" {
  description = "The name of the user assigned managed identity."
  value       = azurerm_user_assigned_identity.this.name
}

output "principal_id" {
  description = "The Principal ID associated with this Managed Service Identity."
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "client_id" {
  description = "The Client ID associated with this Managed Service Identity."
  value       = azurerm_user_assigned_identity.this.client_id
}

output "location" {
  description = "The location of the user assigned managed identity."
  value       = azurerm_user_assigned_identity.this.location
}
