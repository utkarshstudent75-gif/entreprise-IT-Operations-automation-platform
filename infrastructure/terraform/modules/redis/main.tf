resource "azurerm_redis_cache" "this" {
  name                          = var.name
  resource_group_name           = var.resource_group_name
  location                      = var.location
  capacity                      = var.capacity
  family                        = var.family
  sku_name                      = var.sku_name
  non_ssl_port_enabled          = var.non_ssl_port_enabled
  public_network_access_enabled = var.public_network_access_enabled
  minimum_tls_version           = "1.2"
  tags                          = var.tags

  redis_configuration {
    maxmemory_policy = var.maxmemory_policy
  }
}
