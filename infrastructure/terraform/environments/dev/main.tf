
module "groups" {
  source = "../../modules/identity/groups"
  groups = local.organization.groups
}

module "users" {
  source = "../../modules/identity/users"

  users = local.organization.users
}

module "memberships" {
  source           = "../../modules/identity/memberships"
  project_name     = var.project_name
  environment      = var.environment
  users            = local.organization.users
  group_object_ids = module.groups.group_object_ids
  user_object_ids  = module.users.user_object_ids
}

module "app_registration" {
  source       = "../../modules/identity/app-registration"
  project_name = var.project_name
  environment  = var.environment
}

module "app_roles" {
  source                  = "../../modules/identity/app-roles"
  project_name            = var.project_name
  environment             = var.environment
  application_resource_id = module.app_registration.application_resource_id
}

module "role_assignments" {
  source                      = "../../modules/identity/role-assignments"
  project_name                = var.project_name
  environment                 = var.environment
  service_principal_object_id = module.app_registration.service_principal_object_id
  app_role_ids                = module.app_roles.app_role_ids
  group_object_ids            = module.groups.group_object_ids
}

module "resource_group" {
  source = "../../modules/resource-group"

  resource_prefix = local.resource_prefix
  location        = var.location
  tags            = local.common_tags
}

data "azurerm_client_config" "current" {}

resource "random_id" "suffix" {
  byte_length = 4
}

module "virtual_network" {
  source              = "../../modules/virtual-network"
  vnet_name           = "${local.resource_prefix}-vnet"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  address_space       = ["10.10.0.0/16"]
  tags                = local.common_tags
}

module "subnets" {
  source              = "../../modules/subnet"
  resource_group_name = module.resource_group.resource_group_name
  vnet_name           = module.virtual_network.vnet_name
  subnets = {
    aks = {
      name             = "${local.resource_prefix}-aks-subnet"
      address_prefixes = ["10.10.1.0/24"]
    }
    database = {
      name             = "${local.resource_prefix}-db-subnet"
      address_prefixes = ["10.10.2.0/24"]
      delegation = {
        name = "postgres-delegation"
        service_delegation = {
          name    = "Microsoft.DBforPostgreSQL/flexibleServers"
          actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
        }
      }
    }
    private_endpoints = {
      name             = "${local.resource_prefix}-pe-subnet"
      address_prefixes = ["10.10.3.0/24"]
    }
    management = {
      name             = "${local.resource_prefix}-mgmt-subnet"
      address_prefixes = ["10.10.4.0/24"]
    }
    validation = {
      name             = "${local.resource_prefix}-validation-subnet"
      address_prefixes = ["10.10.5.0/24"]
    }
  }
}

module "nsg_aks" {
  source              = "../../modules/network-security-group"
  name                = "${local.resource_prefix}-aks-nsg"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  subnet_id           = module.subnets.subnet_ids["aks"]
  tags                = local.common_tags
  security_rules = [
    {
      name                       = "allow-vnet-inbound"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "VirtualNetwork"
      destination_address_prefix = "VirtualNetwork"
    },
    {
      name                       = "allow-http-inbound"
      priority                   = 110
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "80"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    },
    {
      name                       = "allow-https-inbound"
      priority                   = 120
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "443"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }
  ]
}

module "nsg_database" {
  source              = "../../modules/network-security-group"
  name                = "${local.resource_prefix}-db-nsg"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  subnet_id           = module.subnets.subnet_ids["database"]
  tags                = local.common_tags
  security_rules = [
    {
      name                       = "allow-aks-postgres-inbound"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "5432"
      source_address_prefix      = "10.10.1.0/24"
      destination_address_prefix = "10.10.2.0/24"
    },
    {
      name                       = "deny-all-other-inbound"
      priority                   = 200
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  ]
}

module "nsg_private_endpoints" {
  source              = "../../modules/network-security-group"
  name                = "${local.resource_prefix}-pe-nsg"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  subnet_id           = module.subnets.subnet_ids["private_endpoints"]
  tags                = local.common_tags
  security_rules = [
    {
      name                       = "allow-vnet-inbound"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "VirtualNetwork"
      destination_address_prefix = "VirtualNetwork"
    },
    {
      name                       = "deny-all-other-inbound"
      priority                   = 200
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  ]
}

module "nsg_management" {
  source              = "../../modules/network-security-group"
  name                = "${local.resource_prefix}-mgmt-nsg"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  subnet_id           = module.subnets.subnet_ids["management"]
  tags                = local.common_tags
  security_rules = [
    {
      name                       = "deny-internet-inbound"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Deny"
      protocol                   = "*"
      source_port_range          = "*"
      destination_port_range     = "*"
      source_address_prefix      = "Internet"
      destination_address_prefix = "*"
    }
  ]
}

module "container_registry" {
  source              = "../../modules/container-registry"
  name                = substr(replace(lower("${var.project_name}${var.environment}${random_id.suffix.hex}"), "-", ""), 0, 50)
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  sku                 = "Premium"
  admin_enabled       = false
  tags                = local.common_tags
}

module "storage_account" {
  source                          = "../../modules/storage-account"
  name                            = substr(replace(lower("${var.project_name}${var.environment}${random_id.suffix.hex}"), "-", ""), 0, 24)
  resource_group_name             = module.resource_group.resource_group_name
  location                        = module.resource_group.location
  tags                            = local.common_tags
  allow_nested_items_to_be_public = false
}

module "key_vault" {
  source              = "../../modules/key-vault"
  name                = substr("${local.resource_prefix}-${random_id.suffix.hex}", 0, 24)
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  tags                = local.common_tags
}

module "managed_identity" {
  source              = "../../modules/managed-identity"
  name                = "${local.resource_prefix}-identity"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  tags                = local.common_tags
}

module "log_analytics" {
  source              = "../../modules/log-analytics"
  name                = "${local.resource_prefix}-law"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  retention_in_days   = 30
  tags                = local.common_tags
}

module "monitoring" {
  source              = "../../modules/monitoring"
  name                = "${local.resource_prefix}-insights"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  workspace_id        = module.log_analytics.workspace_id
  tags                = local.common_tags
}

module "private_dns" {
  source              = "../../modules/private-dns"
  resource_group_name = module.resource_group.resource_group_name
  vnet_id             = module.virtual_network.vnet_id
  tags                = local.common_tags
}

module "diagnostics_storage" {
  source                     = "../../modules/diagnostics"
  name                       = "${local.resource_prefix}-storage-diag"
  target_resource_id         = module.storage_account.storage_account_id
  log_analytics_workspace_id = module.log_analytics.workspace_id
}

module "diagnostics_key_vault" {
  source                     = "../../modules/diagnostics"
  name                       = "${local.resource_prefix}-kv-diag"
  target_resource_id         = module.key_vault.key_vault_id
  log_analytics_workspace_id = module.log_analytics.workspace_id
  log_categories             = ["AuditEvent"]
}

module "diagnostics_acr" {
  source                     = "../../modules/diagnostics"
  name                       = "${local.resource_prefix}-acr-diag"
  target_resource_id         = module.container_registry.acr_id
  log_analytics_workspace_id = module.log_analytics.workspace_id
  log_categories             = ["ContainerRegistryRepositoryEvents", "ContainerRegistryLoginEvents"]
}

# NOTE: Resource Groups do not support resource-level Diagnostic Settings in Azure.
# Activity logs are instead captured at the Subscription level.
# module "diagnostics_resource_group" {
#   source                     = "../../modules/diagnostics"
#   name                       = "${local.resource_prefix}-rg-diag"
#   target_resource_id         = module.resource_group.resource_group_id
#   log_analytics_workspace_id = module.log_analytics.workspace_id
# }

#################################
# Phase 3: AKS Cluster and Roles
#################################

module "aks" {
  source              = "../../modules/aks"
  project_name        = var.project_name
  environment         = var.environment
  cluster_name        = "enterprise-dev-aks"
  resource_group_name = module.resource_group.resource_group_name
  location            = module.resource_group.location
  vnet_subnet_id      = module.subnets.subnet_ids["aks"]
  tenant_id           = data.azurerm_client_config.current.tenant_id
  tags                = local.common_tags
  vm_size             = var.vm_size

  # In dev, allow public access with Azure Entra credentials
  api_server_authorized_ip_ranges = []
}

module "acr_role_assignment" {
  source       = "../../modules/acr-role-assignment"
  acr_id       = module.container_registry.acr_id
  principal_id = module.aks.kubelet_identity_object_id
}

module "workload_identity" {
  source                    = "../../modules/workload-identity"
  federated_credential_name = "${local.resource_prefix}-fastapi-fed-cred"
  oidc_issuer_url           = module.aks.oidc_issuer_url
  managed_identity_id       = module.managed_identity.identity_id
  namespace                 = "dev"
  service_account_name      = "fastapi-sa"
}

#################################
# Phase 4A: Managed Data Services
# Enterprise IT Operations Automation Platform
#################################

# 1. Generate Secure Password for PostgreSQL
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# 2. Deploy PostgreSQL Flexible Server
module "postgresql" {
  source                        = "../../modules/postgresql"
  name                          = "${local.resource_prefix}-db-central-${random_id.suffix.hex}"
  resource_group_name           = module.resource_group.resource_group_name
  location                      = "centralus"
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  administrator_username        = var.postgresql_admin_username
  administrator_password        = random_password.db_password.result
  sku_name                      = "B_Standard_B2s"
  storage_mb                    = 32768
  backup_retention_days         = 7
  public_network_access_enabled = true

  firewall_rules = {
    allow_azure_services = {
      start_ip_address = "0.0.0.0"
      end_ip_address   = "0.0.0.0"
    }
  }

  tags = local.common_tags
}

# 3. Deploy Azure Cache for Redis
module "redis" {
  source                        = "../../modules/redis"
  name                          = "${local.resource_prefix}-redis-${random_id.suffix.hex}"
  resource_group_name           = module.resource_group.resource_group_name
  location                      = module.resource_group.location
  sku_name                      = "Basic"
  family                        = "C"
  capacity                      = 0
  non_ssl_port_enabled          = false
  public_network_access_enabled = true
  maxmemory_policy              = "allkeys-lru"

  tags = local.common_tags
}

# 4. Managed Identity RBAC Assignments
# We assign the MI role assignments to Key Vault, Storage Account, and PostgreSQL AD Admin
module "mi_role_assignments" {
  source                         = "../../modules/role-assignments"
  principal_id                   = module.managed_identity.principal_id
  key_vault_id                   = module.key_vault.key_vault_id
  storage_account_id             = module.storage_account.storage_account_id
  enable_postgresql_ad_admin     = true
  postgresql_server_name         = module.postgresql.server_name
  postgresql_resource_group_name = module.resource_group.resource_group_name
  postgresql_admin_tenant_id     = data.azurerm_client_config.current.tenant_id
  postgresql_admin_name          = module.managed_identity.identity_name
}

# Move existing root level role assignments into the new role assignments module
moved {
  from = azurerm_role_assignment.mi_key_vault
  to   = module.mi_role_assignments.azurerm_role_assignment.mi_key_vault
}

moved {
  from = azurerm_role_assignment.mi_storage
  to   = module.mi_role_assignments.azurerm_role_assignment.mi_storage
}

# 5. KV Secrets Officer Assignment for Deployment Principal
# This is required so Terraform can write secrets to Key Vault using RBAC.
resource "azurerm_role_assignment" "deployer_kv_secrets_officer" {
  scope                = module.key_vault.key_vault_id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

# 6. Key Vault Secrets Management
module "keyvault_secrets" {
  source       = "../../modules/keyvault-secrets"
  key_vault_id = module.key_vault.key_vault_id

  secrets = {
    "database-host"            = module.postgresql.server_fqdn
    "database-name"            = var.database_name
    "database-port"            = "5432"
    "database-username"        = var.postgresql_admin_username
    "database-password"        = random_password.db_password.result
    "redis-host"               = module.redis.redis_cache_hostname
    "redis-port"               = tostring(module.redis.redis_cache_ssl_port)
    "redis-primary-key"        = module.redis.redis_cache_primary_access_key
    "msgraph-client-id"        = var.msgraph_client_id
    "msgraph-client-secret"    = var.msgraph_client_secret
    "msgraph-tenant-id"        = var.msgraph_tenant_id
    "sms-provider-api-key"     = var.sms_provider_api_key
    "sms-provider-account-sid" = var.sms_provider_account_sid
  }

  depends_on = [
    azurerm_role_assignment.deployer_kv_secrets_officer
  ]
}

# 7. Optional / Future Private Endpoints Module Preparation
# Conditionally called using the `enable_private_endpoint` toggle.
module "postgresql_private_endpoint" {
  count                          = var.enable_private_endpoint ? 1 : 0
  source                         = "../../modules/private-endpoint"
  name                           = "${local.resource_prefix}-postgres-pe"
  resource_group_name            = module.resource_group.resource_group_name
  location                       = module.resource_group.location
  subnet_id                      = module.subnets.subnet_ids["private_endpoints"]
  private_connection_resource_id = module.postgresql.server_id
  subresource_names              = ["postgresqlServer"]
  private_dns_zone_ids           = [module.private_dns.private_dns_zone_ids["privatelink.postgres.database.azure.com"]]
  tags                           = local.common_tags
}

module "redis_private_endpoint" {
  count                          = var.enable_private_endpoint ? 1 : 0
  source                         = "../../modules/private-endpoint"
  name                           = "${local.resource_prefix}-redis-pe"
  resource_group_name            = module.resource_group.resource_group_name
  location                       = module.resource_group.location
  subnet_id                      = module.subnets.subnet_ids["private_endpoints"]
  private_connection_resource_id = module.redis.redis_cache_id
  subresource_names              = ["redisCache"]
  private_dns_zone_ids           = [module.private_dns.private_dns_zone_ids["privatelink.redis.cache.windows.net"]]
  tags                           = local.common_tags
}


data "azuread_service_principal" "msgraph" {
  client_id = "00000003-0000-0000-c000-000000000000"
}

resource "azuread_app_role_assignment" "mi_msgraph" {
  app_role_id         = data.azuread_service_principal.msgraph.app_role_ids["User.ReadWrite.All"]
  principal_object_id = module.managed_identity.principal_id
  resource_object_id  = data.azuread_service_principal.msgraph.object_id
}

#################################
# Phase 5: Validation Workstation
#################################

# 1. Render configuration startup script
module "startup_script" {
  source        = "../../modules/startup-script"
  dashboard_url = "http://portal.company.com/dashboard"
  timezone      = "Eastern Standard Time"
}

# 2. Generate random local admin password
resource "random_password" "vm_admin_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# 3. Store local admin password in Key Vault
resource "azurerm_key_vault_secret" "vm_admin_password" {
  name         = "validation-vm-admin-password"
  value        = random_password.vm_admin_password.result
  key_vault_id = module.key_vault.key_vault_id
  depends_on   = [azurerm_role_assignment.deployer_kv_secrets_officer]
}

# 4. Deploy Validation Workstation VM
module "validation_workstation" {
  source                  = "../../modules/validation-workstation"
  vm_name                 = "${local.resource_prefix}-val-vm"
  vm_size                 = var.vm_size
  resource_group_name     = module.resource_group.resource_group_name
  location                = module.resource_group.location
  subnet_id               = module.subnets.subnet_ids["validation"]
  admin_username          = "valadmin"
  admin_password          = random_password.vm_admin_password.result
  startup_script_content  = module.startup_script.script_content
  enable_public_ip        = true
  allowed_inbound_rdp_ips = ["*"]
  tags                    = local.common_tags
}

# 5. Assign VM User Login role to Validation Employee in Entra ID
module "vm_identity_assignment" {
  source = "../../modules/identity-assignment"
  scope  = module.validation_workstation.vm_id
  vm_user_login_assignments = {
    "validation-employee" = module.users.user_object_ids["validation-employee"]
  }
  vm_admin_login_assignments = {
    "deployer" = data.azurerm_client_config.current.object_id
  }
}