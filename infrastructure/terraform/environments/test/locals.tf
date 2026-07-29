# Local Values for Test Environment
# Enterprise IT Operations Automation Platform

locals {
  ################################
  # Resource naming
  ################################
  resource_prefix = "${var.project_name}-${var.environment}"

  #################################
  # Common Tags
  #################################
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "entreprise-IT-Operations-automation-platform"
  }

  ##########################
  # Organization Configuration
  ##########################
  organization = yamldecode(
    file("${path.module}/../../data/organization.yaml")
  )

  ###########################
  # Application Roles Configuration
  ###########################
  roles = yamldecode(
    file("${path.module}/../../data/roles.yaml")
  )
}
