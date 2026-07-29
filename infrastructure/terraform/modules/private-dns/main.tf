resource "azurerm_private_dns_zone" "this" {
  for_each            = toset(var.private_dns_zones)
  name                = each.key
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "this" {
  for_each              = azurerm_private_dns_zone.this
  name                  = "${replace(each.key, ".", "-")}-link"
  private_dns_zone_id   = each.value.id
  virtual_network_id    = var.vnet_id
  registration_enabled  = false
  tags                  = var.tags
}
