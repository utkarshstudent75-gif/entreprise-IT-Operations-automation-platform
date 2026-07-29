resource "azurerm_federated_identity_credential" "this" {
  name                      = var.federated_credential_name
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = var.oidc_issuer_url
  user_assigned_identity_id = var.managed_identity_id
  subject                   = "system:serviceaccount:${var.namespace}:${var.service_account_name}"
}
