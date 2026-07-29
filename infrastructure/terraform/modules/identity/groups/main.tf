# Create Microsoft Entra ID groups using the azuread provider.
# Iterates over the var.groups list using a for_each map projection.
resource "azuread_group" "groups" {
  for_each = { for g in var.groups : g.name => g }

  display_name     = each.value.display_name
  description      = each.value.description
  security_enabled = each.value.security_enabled
  mail_enabled     = each.value.mail_enabled

  # Note: Owners are ignored for now as per requirements,
  # and will be implemented in a subsequent phase after user creation.
}
