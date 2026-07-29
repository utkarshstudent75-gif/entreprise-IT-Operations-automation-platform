output "role_assignment_id" {
  description = "The ID of the provisioned Azure Role Assignment."
  value       = azurerm_role_assignment.acr_pull.id
}
