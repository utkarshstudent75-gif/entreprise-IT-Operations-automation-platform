resource "azurerm_role_assignment" "mi_key_vault" {
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = var.principal_id
}

resource "azurerm_role_assignment" "mi_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.principal_id
}

resource "azurerm_postgresql_flexible_server_active_directory_administrator" "mi_postgres" {
  count               = var.enable_postgresql_ad_admin ? 1 : 0
  server_name         = var.postgresql_server_name
  resource_group_name = var.postgresql_resource_group_name
  tenant_id           = var.postgresql_admin_tenant_id
  object_id           = var.principal_id
  principal_name      = var.postgresql_admin_name
  principal_type      = "ServicePrincipal"
}
