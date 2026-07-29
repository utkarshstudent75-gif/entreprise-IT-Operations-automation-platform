# Create Microsoft Entra ID Group Memberships
# Read the groups assigned to each user from organization.yaml and map them dynamically.

locals {
  # Flatten user group memberships into a list of objects
  user_group_memberships = flatten([
    for user in var.users : [
      for group_name in user.groups : {
        user_key   = replace(user.id, " ", "-")
        group_name = group_name
      }
    ]
  ])
}

resource "azuread_group_member" "memberships" {
  for_each = {
    for membership in local.user_group_memberships :
    "${membership.user_key}::${membership.group_name}" => membership
  }

  group_object_id  = var.group_object_ids[each.value.group_name]
  member_object_id = var.user_object_ids[each.value.user_key]
}
