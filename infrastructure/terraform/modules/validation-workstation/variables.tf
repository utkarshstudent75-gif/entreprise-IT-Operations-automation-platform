variable "resource_group_name" {
  type        = string
  description = "The name of the Resource Group to deploy the workstation into."
}

variable "location" {
  type        = string
  description = "The Azure region to deploy the workstation."
}

variable "subnet_id" {
  type        = string
  description = "The ID of the subnet where the VM NIC will reside."
}

variable "vm_name" {
  type        = string
  description = "The name of the Windows VM."
  default     = "val-workstation"
}

variable "admin_username" {
  type        = string
  description = "The admin username for the Windows virtual machine."
  default     = "valadmin"
}

variable "admin_password" {
  type        = string
  description = "The admin password for the Windows virtual machine."
  sensitive   = true
}

variable "enable_public_ip" {
  type        = bool
  description = "Controls if a public IP should be associated with the workstation NIC."
  default     = true
}

variable "allowed_inbound_rdp_ips" {
  type        = list(string)
  description = "CIDR ranges allowed to connect over RDP. Default allows all for validation purposes, but can be restricted."
  default     = ["*"]
}

variable "startup_script_content" {
  type        = string
  description = "The PowerShell configuration script content."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to all workstation resources."
  default     = {}
}

variable "vm_size" {
  type        = string
  description = "The SKU size of the Windows virtual machine."
  default     = "Standard_D2s_v5"
}
