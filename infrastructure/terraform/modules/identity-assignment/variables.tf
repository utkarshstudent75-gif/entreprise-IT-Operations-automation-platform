variable "scope" {
  type        = string
  description = "The scope at which the role assignment should be applied (e.g. the Virtual Machine resource ID)."
}

variable "vm_user_login_assignments" {
  type        = map(string)
  description = "Map of user/group identifier keys to their Microsoft Entra ID principal IDs for VM User Login role."
  default     = {}
}

variable "vm_admin_login_assignments" {
  type        = map(string)
  description = "Map of user/group identifier keys to their Microsoft Entra ID principal IDs for VM Admin Login role."
  default     = {}
}
