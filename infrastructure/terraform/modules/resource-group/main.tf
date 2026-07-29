# Main configuration for the module.
# Resource implementations will be added in the next phase.



resource "azurerm_resource_group" "this" {
  name     = "${var.resource_prefix}-rg"
  location = var.location

  tags = var.tags
}   