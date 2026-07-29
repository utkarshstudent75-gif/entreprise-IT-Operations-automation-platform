# Main configuration for the Microsoft Entra ID App Role Assignments module.
# Iterates over the var.role_assignments list to provision assignments dynamically.

resource "azuread_app_role_assignment" "assignments" {
  for_each = {
    for assignment in var.role_assignments :
    "${assignment.group_name}::${assignment.role_value}" => assignment
  }

  app_role_id         = var.app_role_ids[each.value.role_value]
  principal_object_id = var.group_object_ids[each.value.group_name]
  resource_object_id  = var.service_principal_object_id
}
