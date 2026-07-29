output "memberships" {
  description = "A map of created group memberships."
  value = {
    for k, v in azuread_group_member.memberships : k => {
      group_object_id  = v.group_object_id
      member_object_id = v.member_object_id
    }
  }
}
