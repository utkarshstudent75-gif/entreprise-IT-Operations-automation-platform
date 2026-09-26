#!/usr/bin/env bash

# Sourcing helpers
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/_common.sh"

set -Eeuo pipefail

log_warn "========================================================="
log_warn "  Enterprise IT Operations Platform - Cleanup Script     "
log_warn "========================================================="
log_warn "  WARNING: This script contains highly destructive actions."
log_warn "========================================================="

# Load environment defaults if available
JSON_FILE="${SCRIPT_DIR}/.bootstrap-output.json"
BACKEND_RG="${EITOAP_BACKEND_RG:-eitoap-tfstate-rg}"
BACKEND_STORAGE="${EITOAP_BACKEND_STORAGE:-}"
PROJECT_NAME="${EITOAP_PROJECT_NAME:-eitoap}"
ENVIRONMENT="${EITOAP_ENVIRONMENT:-dev}"
DEV_RG="${PROJECT_NAME}-${ENVIRONMENT}-rg"

if [[ -f "$JSON_FILE" ]]; then
    BACKEND_RG=$(jq -r '.TF_BACKEND_RG // "eitoap-tfstate-rg"' "$JSON_FILE")
    BACKEND_STORAGE=$(jq -r '.TF_BACKEND_STORAGE // empty' "$JSON_FILE")
    DEV_RG=$(jq -r '.RESOURCE_GROUP // "eitoap-dev-rg"' "$JSON_FILE")
fi

# Clean up dev environment resources
cleanup_dev_resources() {
    log_info "Attempting to destroy Terraform-managed development infrastructure..."
    
    TF_DEV_DIR="${SCRIPT_DIR}/../infrastructure/terraform/environments/${ENVIRONMENT}"
    if [[ -d "$TF_DEV_DIR" ]]; then
        cd "$TF_DEV_DIR"
        
        # Verify if initialized
        if [[ -d ".terraform" ]]; then
            if confirm_action "Are you sure you want to run 'terraform destroy' in '$ENVIRONMENT'?" "N"; then
                log_warn "Destroying infrastructure..."
                terraform destroy -auto-approve || {
                    log_error "Terraform destroy failed. Running resource group force deletion as fallback..."
                }
            fi
        else
            log_warn "Terraform not initialized in '$TF_DEV_DIR'. Cannot run terraform destroy."
        fi
    else
        log_warn "Terraform dev environment directory '$TF_DEV_DIR' does not exist."
    fi
    
    # Check if resource group still exists and delete it
    if az group show --name "$DEV_RG" >/dev/null 2>&1; then
        if confirm_action "Azure Resource Group '$DEV_RG' still exists. Force delete it?" "N"; then
            log_warn "Deleting Resource Group '$DEV_RG'..."
            az group delete --name "$DEV_RG" --yes --no-wait
            log_success "Initiated deletion of Resource Group '$DEV_RG'."
        fi
    else
        log_info "Azure Resource Group '$DEV_RG' already deleted or does not exist."
    fi
}

# Clean up state backend
cleanup_backend() {
    log_info "Attempting to clean up Terraform state backend..."
    
    if [[ -n "$BACKEND_STORAGE" ]]; then
        log_info "Storage Account detected: $BACKEND_STORAGE"
    fi
    
    if az group show --name "$BACKEND_RG" >/dev/null 2>&1; then
        if confirm_action "Are you sure you want to delete the state Resource Group '$BACKEND_RG' and storage account?" "N"; then
            log_warn "Deleting backend Resource Group '$BACKEND_RG'..."
            az group delete --name "$BACKEND_RG" --yes
            log_success "Backend Resource Group '$BACKEND_RG' deleted successfully."
            
            # Remove metadata file
            if [[ -f "$JSON_FILE" ]]; then
                rm -f "$JSON_FILE"
                log_info "Cleaned up local metadata bootstrap-output.json."
            fi
        fi
    else
        log_info "Backend Resource Group '$BACKEND_RG' does not exist."
    fi
}

# Clean up AKS Kubernetes workloads
cleanup_k8s_workloads() {
    log_info "Attempting to clean up Kubernetes namespace resources (helm charts)..."
    
    if kubectl cluster-info >/dev/null 2>&1; then
        if confirm_action "Are you sure you want to delete all Helm releases and custom namespaces?" "N"; then
            log_warn "Deleting frontend, backend, and common Helm releases..."
            helm uninstall frontend -n frontend 2>/dev/null || true
            helm uninstall backend -n backend 2>/dev/null || true
            helm uninstall common -n database 2>/dev/null || true
            
            log_warn "Deleting namespaces..."
            kubectl delete namespace frontend backend database 2>/dev/null || true
            log_success "Kubernetes workload cleanup completed."
        fi
    else
        log_error "Unable to connect to Kubernetes cluster. Skip workloads deletion."
    fi
}

# Menu selection
show_menu() {
    echo "---------------------------------------------------------"
    echo "Please choose a cleanup option:"
    echo "1) Destroy Development Environment (Terraform resources + RG)"
    echo "2) Delete Terraform State Backend (Resource Group + Storage Account)"
    echo "3) Delete Kubernetes Workloads only (Helm releases + Namespaces)"
    echo "4) Destroy All (Dev Environment + K8s Workloads + State Backend)"
    echo "5) Cancel / Exit"
    echo "---------------------------------------------------------"
    echo -n "Enter option [1-5]: "
    read -r choice
    
    case "$choice" in
        1)
            cleanup_dev_resources
            ;;
        2)
            cleanup_backend
            ;;
        3)
            cleanup_k8s_workloads
            ;;
        4)
            log_warn "CRITICAL WARNING: This will destroy the entire deployment including state history!"
            if confirm_action "Proceed with full destruction?" "N"; then
                cleanup_k8s_workloads
                cleanup_dev_resources
                cleanup_backend
                log_success "Full cleanup process finished."
            fi
            ;;
        5|*)
            log_info "Cleanup cancelled. Exiting..."
            exit 0
            ;;
    esac
}

# Run menu
show_menu