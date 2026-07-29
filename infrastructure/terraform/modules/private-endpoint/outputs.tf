output "private_endpoint_id" {
  description = "The ID of the private endpoint."
  value       = azurerm_private_endpoint.this.id
}

output "private_endpoint_name" {
  description = "The name of the private endpoint."
  value       = azurerm_private_endpoint.this.name
}

output "private_ip_address" {
  description = "The private IP address of the endpoint."
  value       = azurerm_private_endpoint.this.private_service_connection[0].private_ip_address
}

output "location" {
  description = "The location of the private endpoint."
  value       = azurerm_private_endpoint.this.location
}
