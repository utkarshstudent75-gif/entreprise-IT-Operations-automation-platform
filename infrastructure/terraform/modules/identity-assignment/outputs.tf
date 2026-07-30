output "user_login_assignment_ids" {
  description = "IDs of the Virtual Machine User Login role assignments."
  value       = { for k, v in azurerm_role_assignment.user_login : k => v.id }
}

output "admin_login_assignment_ids" {
  description = "IDs of the Virtual Machine Administrator Login role assignments."
  value       = { for k, v in azurerm_role_assignment.admin_login : k => v.id }
}
