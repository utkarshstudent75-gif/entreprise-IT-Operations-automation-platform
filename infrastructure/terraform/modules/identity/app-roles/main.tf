# Main configuration for the Microsoft Entra ID App Roles module.
# Iterates over the var.app_roles map to provision the required roles.

# Create stable GUIDs for the application roles
resource "random_uuid" "role_ids" {
  for_each = var.app_roles
}

# Create Microsoft Entra ID App Roles using the azuread provider
resource "azuread_application_app_role" "app_roles" {
  for_each = var.app_roles

  application_id       = var.application_resource_id
  role_id              = random_uuid.role_ids[each.key].result
  allowed_member_types = each.value.allowed_member_types
  description          = each.value.description
  display_name         = each.value.display_name
  value                = each.value.value
}
