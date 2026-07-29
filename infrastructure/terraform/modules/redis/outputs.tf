output "redis_cache_id" {
  description = "The ID of the Redis Cache."
  value       = azurerm_redis_cache.this.id
}

output "redis_cache_hostname" {
  description = "The FQDN / hostname of the Redis Cache."
  value       = azurerm_redis_cache.this.hostname
}

output "redis_cache_ssl_port" {
  description = "The SSL Port of the Redis Cache."
  value       = azurerm_redis_cache.this.ssl_port
}

output "redis_cache_primary_access_key" {
  description = "The Primary Access Key for the Redis Cache."
  value       = azurerm_redis_cache.this.primary_access_key
  sensitive   = true
}
