variable "scope" {
  type        = string
  description = "The scope at which the role assignment should be applied (e.g. the Virtual Machine resource ID)."
}

variable "vm_user_login_principal_ids" {
  type        = list(string)
  description = "List of Microsoft Entra ID principal IDs (users/groups) to be assigned the 'Virtual Machine User Login' role."
  default     = []
}

variable "vm_admin_login_principal_ids" {
  type        = list(string)
  description = "List of Microsoft Entra ID principal IDs (users/groups) to be assigned the 'Virtual Machine Administrator Login' role."
  default     = []
}
