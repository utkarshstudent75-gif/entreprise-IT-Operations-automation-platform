terraform {
  # The backend block configuration is kept empty so it can be dynamically
  # configured during `terraform init -backend-config=...` in CI/CD pipelines,
  # or customized per developer workspace.
  backend "azurerm" {}
}
