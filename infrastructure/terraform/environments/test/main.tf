module "groups" {
  source = "../../modules/identity/groups"
  groups = local.organization.groups
}

module "users" {
  source = "../../modules/identity/users"

  users = local.organization.users
}

module "memberships" {
  source           = "../../modules/identity/memberships"
  project_name     = var.project_name
  environment      = var.environment
  users            = local.organization.users
  group_object_ids = module.groups.group_object_ids
  user_object_ids  = module.users.user_object_ids
}

module "app_registration" {
  source       = "../../modules/identity/app-registration"
  project_name = var.project_name
  environment  = var.environment
}

module "app_roles" {
  source                  = "../../modules/identity/app-roles"
  project_name            = var.project_name
  environment             = var.environment
  application_resource_id = module.app_registration.application_resource_id
}

module "role_assignments" {
  source                      = "../../modules/identity/role-assignments"
  project_name                = var.project_name
  environment                 = var.environment
  service_principal_object_id = module.app_registration.service_principal_object_id
  app_role_ids                = module.app_roles.app_role_ids
  group_object_ids            = module.groups.group_object_ids
}

module "resource_group" {
  source = "../../modules/resource-group"

  resource_prefix = local.resource_prefix
  location        = var.location
  tags            = local.common_tags
}
