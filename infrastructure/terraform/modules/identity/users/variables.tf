
variable "users" {

  description = "List of Microsoft Entra ID users to create"


  type = list(object({

    id              = string
    first_name      = string
    last_name       = string
    display_name    = string
    email           = string
    department      = string
    job_title       = string
    manager         = optional(string)
    account_enabled = bool
    groups          = list(string)

  }))

  validation {
    condition = length(var.users) == length(distinct([
      for user in var.users : user.email
    ]))

    error_message = "Each user email must be unique."
  }

  validation {
    condition = alltrue([
      for user in var.users :
      trimspace(user.display_name) != ""
    ])

    error_message = "Display name cannot be empty."
  }

  validation {
    condition = length(var.users) == length(distinct([
      for user in var.users : user.id
    ]))

    error_message = "Each user ID must be unique."
  }

}