output "subnet_ids" {
  description = "A map of subnet keys to their Azure resource IDs."
  value       = { for k, v in azurerm_subnet.this : k => v.id }
}

output "subnet_names" {
  description = "A map of subnet keys to their names."
  value       = { for k, v in azurerm_subnet.this : k => v.name }
}

output "subnet_address_prefixes" {
  description = "A map of subnet keys to their address prefixes."
  value       = { for k, v in azurerm_subnet.this : k => v.address_prefixes }
}
