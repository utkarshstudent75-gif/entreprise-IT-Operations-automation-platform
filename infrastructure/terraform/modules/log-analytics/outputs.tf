output "workspace_id" {
  description = "The ID of the Log Analytics Workspace."
  value       = azurerm_log_analytics_workspace.this.id
}

output "workspace_workspace_id" {
  description = "The Workspace ID (client ID) of the Log Analytics Workspace."
  value       = azurerm_log_analytics_workspace.this.workspace_id
}

output "workspace_name" {
  description = "The name of the Log Analytics Workspace."
  value       = azurerm_log_analytics_workspace.this.name
}

output "location" {
  description = "The location of the Log Analytics Workspace."
  value       = azurerm_log_analytics_workspace.this.location
}
