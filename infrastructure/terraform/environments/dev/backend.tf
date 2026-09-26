terraform {

  backend "azurerm" {
    resource_group_name  = "eitoap-tfstate-rg"
    storage_account_name = "eitoaptfstate"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }


}
