# Root-level outputs exposing useful identifiers from identity modules.

output "groups" {
  description = "A map of group names to their Azure AD object IDs."
  value       = module.groups.group_object_ids
}

output "users" {
  description = "A map of user account names to their Azure AD user principal names."
  value       = module.users.user_principal_names
}

output "app_registration" {
  description = "Application registration details."
  value = {
    application_resource_id     = module.app_registration.application_resource_id
    client_id                   = module.app_registration.client_id
    object_id                   = module.app_registration.object_id
    service_principal_object_id = module.app_registration.service_principal_object_id
  }
}

output "app_roles" {
  description = "Created application roles and their GUID IDs."
  value       = module.app_roles.app_role_ids
}

output "memberships" {
  description = "Provisioned group memberships count."
  value       = length(module.memberships.memberships)
}

output "role_assignments" {
  description = "Provisioned role assignments count."
  value       = length(module.role_assignments.role_assignments)
}

output "vnet_id" {
  description = "The ID of the virtual network."
  value       = module.virtual_network.vnet_id
}

output "vnet_name" {
  description = "The name of the virtual network."
  value       = module.virtual_network.vnet_name
}

output "subnet_ids" {
  description = "A map of subnet keys to their Azure resource IDs."
  value       = module.subnets.subnet_ids
}

output "acr_id" {
  description = "The ID of the Container Registry."
  value       = module.container_registry.acr_id
}

output "acr_name" {
  description = "The name of the Container Registry."
  value       = module.container_registry.acr_name
}

output "acr_login_server" {
  description = "The URL that can be used to log into the container registry."
  value       = module.container_registry.acr_login_server
}

output "storage_account_id" {
  description = "The ID of the storage account."
  value       = module.storage_account.storage_account_id
}

output "storage_account_name" {
  description = "The name of the storage account."
  value       = module.storage_account.storage_account_name
}

output "key_vault_id" {
  description = "The ID of the Key Vault."
  value       = module.key_vault.key_vault_id
}

output "key_vault_name" {
  description = "The name of the Key Vault."
  value       = module.key_vault.key_vault_name
}

output "key_vault_uri" {
  description = "The URI of the Key Vault."
  value       = module.key_vault.key_vault_uri
}

output "managed_identity_id" {
  description = "The ID of the managed identity."
  value       = module.managed_identity.identity_id
}

output "managed_identity_principal_id" {
  description = "The Principal ID of the managed identity."
  value       = module.managed_identity.principal_id
}

output "managed_identity_client_id" {
  description = "The Client ID of the managed identity."
  value       = module.managed_identity.client_id
}

output "log_analytics_workspace_id" {
  description = "The ID of the Log Analytics Workspace."
  value       = module.log_analytics.workspace_id
}

output "log_analytics_workspace_workspace_id" {
  description = "The Workspace ID (client ID) of the Log Analytics Workspace."
  value       = module.log_analytics.workspace_workspace_id
}

output "app_insights_id" {
  description = "The ID of the Application Insights resource."
  value       = module.monitoring.app_insights_id
}

output "private_dns_zone_ids" {
  description = "A map of Private DNS zone names to their resource IDs."
  value       = module.private_dns.private_dns_zone_ids
}

#################################
# Phase 3: AKS Cluster Outputs
#################################

output "aks_cluster_name" {
  description = "The name of the AKS cluster."
  value       = module.aks.cluster_name
}

output "aks_cluster_id" {
  description = "The resource ID of the AKS cluster."
  value       = module.aks.cluster_id
}

output "aks_oidc_issuer_url" {
  description = "The OIDC issuer URL of the AKS cluster."
  value       = module.aks.oidc_issuer_url
}

output "aks_node_resource_group" {
  description = "The auto-generated Resource Group containing AKS cluster agent resources."
  value       = module.aks.node_resource_group
}

output "aks_kubeconfig" {
  description = "Raw kubeconfig configuration for the AKS cluster."
  value       = module.aks.kube_config_raw
  sensitive   = true
}

output "db_host" {
  description = "The database host name."
  value       = module.postgresql.server_name
}

output "db_fqdn" {
  description = "The database fully qualified domain name."
  value       = module.postgresql.server_fqdn
}

output "redis_host" {
  description = "The Redis Cache hostname."
  value       = module.redis.redis_cache_hostname
}

output "redis_port" {
  description = "The Redis Cache SSL port."
  value       = module.redis.redis_cache_ssl_port
}

output "postgresql_connection_string" {
  description = "Connection string for PostgreSQL (without password)."
  value       = "Host=${module.postgresql.server_fqdn};Port=5432;Database=${var.database_name};Username=${var.postgresql_admin_username};SSL Mode=Require;"
}

output "redis_connection_string" {
  description = "Connection string for Redis (without password)."
  value       = "rediss://${module.redis.redis_cache_hostname}:${module.redis.redis_cache_ssl_port}"
}

#################################
# Validation Workstation Outputs
#################################

output "validation_workstation_name" {
  description = "The name of the validation workstation VM."
  value       = module.validation_workstation.vm_name
}

output "validation_workstation_public_ip" {
  description = "The public IP address of the validation workstation VM."
  value       = module.validation_workstation.public_ip
}

output "validation_workstation_private_ip" {
  description = "The private IP address of the validation workstation VM."
  value       = module.validation_workstation.private_ip
}




