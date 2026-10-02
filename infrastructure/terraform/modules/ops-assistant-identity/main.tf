resource "azurerm_user_assigned_identity" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

resource "azurerm_federated_identity_credential" "this" {
  name                      = "${var.name}-federated"
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = var.oidc_issuer_url
  user_assigned_identity_id = azurerm_user_assigned_identity.this.id
  subject                   = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
}

locals {
  assignments = merge(
    {
      subscription_reader = {
        scope = "/subscriptions/${var.subscription_id}"
        role  = "Reader"
      }
      subscription_monitoring_reader = {
        scope = "/subscriptions/${var.subscription_id}"
        role  = "Monitoring Reader"
      }
      subscription_log_analytics_reader = {
        scope = "/subscriptions/${var.subscription_id}"
        role  = "Log Analytics Reader"
      }
    }
  )
}

resource "azurerm_role_assignment" "read_only_monitoring" {
  for_each             = local.assignments
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = azurerm_user_assigned_identity.this.principal_id
  principal_type       = "ServicePrincipal"
}
