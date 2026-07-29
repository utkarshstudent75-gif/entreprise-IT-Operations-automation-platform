# Outputs for the module will be defined here as resources are implemented.
output "user_ids" {
  description = "Map of user IDs to Azure AD user IDs."

  value = {
    for key, user in azuread_user.users :
    key => user.id
  }
}


output "user_object_ids" {
  description = "Map of user IDs to Azure AD object IDs."

  value = {
    for key, user in azuread_user.users :
    key => user.object_id
  }
}

output "user_principal_names" {
  description = "Map of user IDs to User Principal Names."

  value = {
    for key, user in azuread_user.users :
    key => user.user_principal_name
  }
}

