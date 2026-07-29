output "app_role_ids" {
  description = "A map of app role values (e.g., 'Platform.Admin') to their role ID GUIDs."
  value       = { for k, v in azuread_application_app_role.app_roles : v.value => v.role_id }
}

output "app_role_display_names" {
  description = "A map of app role values to their display names."
  value       = { for k, v in azuread_application_app_role.app_roles : v.value => v.display_name }
}

output "role_objects" {
  description = "A map of app role keys to their complete resource attributes."
  value       = azuread_application_app_role.app_roles
}
