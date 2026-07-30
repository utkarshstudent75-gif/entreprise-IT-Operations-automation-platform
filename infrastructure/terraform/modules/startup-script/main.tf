locals {
  script_content = templatefile("${path.module}/templates/configure-vm.ps1.tmpl", {
    dashboard_url = var.dashboard_url
    timezone      = var.timezone
  })
}
