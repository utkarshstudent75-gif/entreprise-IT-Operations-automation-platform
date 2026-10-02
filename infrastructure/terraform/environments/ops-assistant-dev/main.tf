locals {
  project_name    = "enterprise-it-operations-platform"
  environment     = "dev"
  resource_prefix = "${local.project_name}-${local.environment}"

  common_tags = {
    Project     = local.project_name
    Environment = local.environment
    ManagedBy   = "Terraform"
    Repository  = "entreprise-IT-Operations-automation-platform"
  }
}

data "azurerm_resource_group" "application" {
  name = var.application_resource_group_name
}

module "ops_assistant_identity" {
  source               = "../../modules/ops-assistant-identity"
  name                 = "${local.resource_prefix}-ops-assistant-identity"
  resource_group_name  = data.azurerm_resource_group.application.name
  location             = var.location
  tags                 = local.common_tags
  oidc_issuer_url      = var.oidc_issuer_url
  namespace            = "backend"
  service_account_name = "ops-assistant"
  subscription_id      = var.subscription_id
}
