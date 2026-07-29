terraform {

  backend "azurerm" {
    resource_group_name  = "enterprise-itops-dev-rg"
    storage_account_name = "eitoap75"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }


}
