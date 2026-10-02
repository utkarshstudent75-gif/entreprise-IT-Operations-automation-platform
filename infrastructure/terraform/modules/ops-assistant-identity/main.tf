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
  read_roles = toset(["Reader", "Monitoring Reader"])
  assignments = {
    for pair in setproduct(keys(var.monitoring_resource_group_ids), local.read_roles) :
    "${pair[0]}-${replace(pair[1], " ", "-")}" => {
      scope = var.monitoring_resource_group_ids[pair[0]]
      role  = pair[1]
    }
  }
}

resource "azurerm_role_assignment" "read_only_monitoring" {
  for_each             = local.assignments
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = azurerm_user_assigned_identity.this.principal_id
  principal_type       = "ServicePrincipal"
}
