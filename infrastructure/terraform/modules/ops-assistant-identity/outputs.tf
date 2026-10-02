output "identity_id" {
  description = "Resource ID of the dedicated operations-assistant managed identity."
  value       = azurerm_user_assigned_identity.this.id
}

output "identity_client_id" {
  description = "Client ID used by the backend Helm service account."
  value       = azurerm_user_assigned_identity.this.client_id
}

output "identity_principal_id" {
  description = "Principal ID of the read-only operations-assistant identity."
  value       = azurerm_user_assigned_identity.this.principal_id
}
