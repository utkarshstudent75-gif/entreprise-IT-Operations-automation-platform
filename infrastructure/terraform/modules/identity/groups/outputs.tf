# Outputs for the Microsoft Entra ID Groups module.
# Return values are maps keyed by the group name.

output "group_ids" {
  description = "A map of group names to their resource IDs."
  value       = { for k, v in azuread_group.groups : k => v.id }
}

output "group_object_ids" {
  description = "A map of group names to their Azure Active Directory object IDs."
  value       = { for k, v in azuread_group.groups : k => v.object_id }
}

output "group_display_names" {
  description = "A map of group names to their display names."
  value       = { for k, v in azuread_group.groups : k => v.display_name }
}
