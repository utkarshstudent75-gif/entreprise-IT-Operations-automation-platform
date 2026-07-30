# Identity Assignment Module (Azure RBAC VM Access)

resource "azurerm_role_assignment" "user_login" {
  for_each             = toset(var.vm_user_login_principal_ids)
  scope                = var.scope
  role_definition_name = "Virtual Machine User Login"
  principal_id         = each.value
}

resource "azurerm_role_assignment" "admin_login" {
  for_each             = toset(var.vm_admin_login_principal_ids)
  scope                = var.scope
  role_definition_name = "Virtual Machine Administrator Login"
  principal_id         = each.value
}
