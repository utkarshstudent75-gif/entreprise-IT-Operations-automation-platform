output "app_insights_id" {
  description = "The ID of the Application Insights resource."
  value       = azurerm_application_insights.this.id
}

output "app_insights_name" {
  description = "The name of the Application Insights resource."
  value       = azurerm_application_insights.this.name
}

output "instrumentation_key" {
  description = "The Instrumentation Key of the Application Insights resource."
  value       = azurerm_application_insights.this.instrumentation_key
  sensitive   = true
}

output "connection_string" {
  description = "The Connection String of the Application Insights resource."
  value       = azurerm_application_insights.this.connection_string
  sensitive   = true
}

output "location" {
  description = "The location of the Application Insights resource."
  value       = azurerm_application_insights.this.location
}
