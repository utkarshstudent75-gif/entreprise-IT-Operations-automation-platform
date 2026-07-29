az aks stop --name enterprise-dev-aks --resource-group enterprise-it-operations-platform-dev-rg


az aks start --name enterprise-dev-aks --resource-group enterprise-it-operations-platform-dev-rg


Switch the AKS node VM size to Standard_B2s (2 vCPU, 4GB RAM, ~$30/month) or Standard_D2as_v5 (AMD-equivalent, slightly cheaper) by editing the vm_size input in terraform.tfvars.