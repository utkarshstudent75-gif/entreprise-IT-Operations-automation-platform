output "private_dns_zone_ids" {
  description = "A map of Private DNS zone names to their resource IDs."
  value       = { for k, v in azurerm_private_dns_zone.this : k => v.id }
}

output "private_dns_zone_names" {
  description = "A list of Private DNS zone names."
  value       = [for k, v in azurerm_private_dns_zone.this : v.name]
}
