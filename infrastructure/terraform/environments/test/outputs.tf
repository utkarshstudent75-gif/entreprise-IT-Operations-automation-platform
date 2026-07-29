# Root-level outputs exposing useful identifiers from identity modules.

output "groups" {
  description = "A map of group names to their Azure AD object IDs."
  value       = module.groups.group_object_ids
}

output "users" {
  description = "A map of user account names to their Azure AD user principal names."
  value       = module.users.user_principal_names
}

output "app_registration" {
  description = "Application registration details."
  value = {
    application_resource_id     = module.app_registration.application_resource_id
    client_id                   = module.app_registration.client_id
    object_id                   = module.app_registration.object_id
    service_principal_object_id = module.app_registration.service_principal_object_id
  }
}

output "app_roles" {
  description = "Created application roles and their GUID IDs."
  value       = module.app_roles.app_role_ids
}

output "memberships" {
  description = "Provisioned group memberships count."
  value       = length(module.memberships.memberships)
}

output "role_assignments" {
  description = "Provisioned role assignments count."
  value       = length(module.role_assignments.role_assignments)
}
