resource "azurerm_kubernetes_cluster" "this" {
  name                    = var.cluster_name
  location                = var.location
  resource_group_name     = var.resource_group_name
  dns_prefix              = coalesce(var.dns_prefix, var.cluster_name)
  private_cluster_enabled = false

  # Cost Optimization: Free tier control plane
  sku_tier = "Free"

  # Entra Integration and Azure RBAC
  local_account_disabled = true

  azure_active_directory_role_based_access_control {
    tenant_id          = var.tenant_id
    azure_rbac_enabled = true
  }

  # OIDC and Workload Identity
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  default_node_pool {
    name                        = "system"
    node_count                  = var.node_count
    vm_size                     = var.vm_size
    vnet_subnet_id              = var.vnet_subnet_id
    auto_scaling_enabled        = true
    min_count                   = var.min_count
    max_count                   = var.max_count
    type                        = "VirtualMachineScaleSets"
    temporary_name_for_rotation = "systemtemp"
    tags                        = var.tags
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    pod_cidr            = var.pod_cidr
    service_cidr        = var.service_cidr
    dns_service_ip      = var.dns_service_ip
    outbound_type       = "loadBalancer"
  }

  # API Server Authorized IP Ranges (only applied if the list is not empty)
  api_server_access_profile {
    authorized_ip_ranges = length(var.api_server_authorized_ip_ranges) > 0 ? var.api_server_authorized_ip_ranges : null
  }

  tags = var.tags
}
