# Main configuration for the module.
# Resource implementations will be added in the next phase.

resource "random_password" "user_passwords" {
  for_each = {

    for user in var.users : replace(user.id, " ", "-") => user
  }

  length           = 20
  special          = true
  override_special = "!@#$%^&*"

}

resource "azuread_user" "users" {
  for_each = {
    for user in var.users : replace(user.id, " ", "-") => user
  }

  user_principal_name = each.value.email
  display_name        = each.value.display_name
  mail_nickname       = split("@", each.value.email)[0]

  password = random_password.user_passwords[each.key].result

  account_enabled = each.value.account_enabled

  department = each.value.department
  job_title  = each.value.job_title

  force_password_change = true
}