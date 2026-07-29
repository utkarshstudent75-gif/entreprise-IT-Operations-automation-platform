output "acr_id" {
  description = "The ID of the Container Registry."
  value       = azurerm_container_registry.this.id
}

output "acr_name" {
  description = "The name of the Container Registry."
  value       = azurerm_container_registry.this.name
}

output "acr_login_server" {
  description = "The URL that can be used to log into the container registry."
  value       = azurerm_container_registry.this.login_server
}

output "location" {
  description = "The location of the Container Registry."
  value       = azurerm_container_registry.this.location
}
