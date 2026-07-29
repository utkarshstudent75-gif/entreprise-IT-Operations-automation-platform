output "mi_key_vault_role_assignment_id" {
  description = "The ID of the Key Vault Secrets User role assignment."
  value       = azurerm_role_assignment.mi_key_vault.id
}

output "mi_storage_role_assignment_id" {
  description = "The ID of the Storage Blob Data Contributor role assignment."
  value       = azurerm_role_assignment.mi_storage.id
}

output "mi_postgres_ad_admin_id" {
  description = "The ID of the PostgreSQL Active Directory administrator resource."
  value       = length(azurerm_postgresql_flexible_server_active_directory_administrator.mi_postgres) > 0 ? azurerm_postgresql_flexible_server_active_directory_administrator.mi_postgres[0].id : null
}
