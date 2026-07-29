# Main configuration for the Microsoft Entra ID App Registration module.

data "azuread_client_config" "current" {}

resource "azuread_application" "app" {
  display_name = "${var.display_name} (${upper(var.environment)})"
  owners       = [data.azuread_client_config.current.object_id]

  # Prevent conflicts with standalone app roles managed by the app-roles module
  lifecycle {
    ignore_changes = [
      app_role
    ]
  }
}

resource "azuread_service_principal" "sp" {
  client_id = azuread_application.app.client_id
  owners    = [data.azuread_client_config.current.object_id]
}
