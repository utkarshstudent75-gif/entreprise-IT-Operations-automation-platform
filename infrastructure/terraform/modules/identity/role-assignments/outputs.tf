output "role_assignments" {
  description = "A map of the created role assignments, detailing the principal, role, and resource."
  value = {
    for k, v in azuread_app_role_assignment.assignments : k => {
      principal_object_id = v.principal_object_id
      app_role_id         = v.app_role_id
      resource_object_id  = v.resource_object_id
    }
  }
}
