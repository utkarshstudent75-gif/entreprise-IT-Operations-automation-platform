variable "project_name" {
  type        = string
  description = "The name of the project, used for resource naming and tagging."
}

variable "environment" {
  type        = string
  description = "The target deployment environment (dev, test, prod)."
}

variable "cluster_name" {
  type        = string
  description = "The name of the AKS cluster."
}

variable "resource_group_name" {
  type        = string
  description = "The name of the resource group to deploy the cluster in."
}

variable "location" {
  type        = string
  description = "The Azure region to deploy the cluster in."
}

variable "vnet_subnet_id" {
  type        = string
  description = "The resource ID of the existing subnet where the default node pool should be placed."
}

variable "dns_prefix" {
  type        = string
  description = "The DNS prefix for the AKS cluster. If omitted, will be constructed from the cluster name."
  default     = ""
}

variable "node_count" {
  type        = number
  description = "The initial number of nodes in the system node pool."
  default     = 1
}

variable "min_count" {
  type        = number
  description = "The minimum number of nodes for the system node pool autoscaler."
  default     = 1
}

variable "max_count" {
  type        = number
  description = "The maximum number of nodes for the system node pool autoscaler."
  default     = 3
}

variable "vm_size" {
  type        = string
  description = "The VM size to use for nodes in the system node pool."
  default     = "Standard_D2s_v7"
}

variable "api_server_authorized_ip_ranges" {
  type        = list(string)
  description = "The IP ranges authorized to access the AKS API server."
  default     = []
}

variable "tags" {
  type        = map(string)
  description = "A mapping of tags to assign to the resource."
  default     = {}
}

variable "pod_cidr" {
  type        = string
  description = "CIDR range for Kubernetes pods when using CNI Overlay."
  default     = "10.244.0.0/16"
}

variable "service_cidr" {
  type        = string
  description = "CIDR range for Kubernetes services."
  default     = "10.96.0.0/16"
}

variable "dns_service_ip" {
  type        = string
  description = "IP address within the service CIDR range for the Kubernetes DNS service."
  default     = "10.96.0.10"
}

variable "tenant_id" {
  type        = string
  description = "The tenant ID for Azure Active Directory integration."
}

