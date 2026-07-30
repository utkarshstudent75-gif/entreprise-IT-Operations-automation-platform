# Identity Assignment Module (Azure RBAC VM Access)

resource "azurerm_role_assignment" "user_login" {
  for_each             = var.vm_user_login_assignments
  scope                = var.scope
  role_definition_name = "Virtual Machine User Login"
  principal_id         = each.value
}

resource "azurerm_role_assignment" "admin_login" {
  for_each             = var.vm_admin_login_assignments
  scope                = var.scope
  role_definition_name = "Virtual Machine Administrator Login"
  principal_id         = each.value
}
