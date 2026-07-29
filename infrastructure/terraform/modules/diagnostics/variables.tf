variable "name" {
  type        = string
  description = "The name of the diagnostic setting."
}

variable "target_resource_id" {
  type        = string
  description = "The ID of the target resource."
}

variable "log_analytics_workspace_id" {
  type        = string
  description = "The ID of the Log Analytics Workspace where diagnostics data should be sent."
}

variable "log_categories" {
  type        = list(string)
  description = "A list of log categories to enable."
  default     = []
}

variable "metric_categories" {
  type        = list(string)
  description = "A list of metric categories to enable."
  default     = ["AllMetrics"]
}
