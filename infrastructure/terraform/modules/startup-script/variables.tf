variable "dashboard_url" {
  type        = string
  description = "The URL of the EITOAP dashboard to open automatically on login."
}

variable "timezone" {
  type        = string
  description = "The timezone configuration for the validation workstation."
  default     = "Eastern Standard Time"
}
