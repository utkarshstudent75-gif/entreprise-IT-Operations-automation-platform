#!/usr/bin/env bash

# Sourcing helpers
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/_common.sh"

set -Eeuo pipefail

log_success "========================================================="
log_success "  Enterprise IT Operations Platform - Verification Script "
log_success "========================================================="

# Load environment defaults if available
JSON_FILE="${SCRIPT_DIR}/.bootstrap-output.json"
RESOURCE_GROUP="${RESOURCE_GROUP:-}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-}"
ACR_NAME="${ACR_NAME:-}"
KEYVAULT_NAME="${KEYVAULT_NAME:-}"
POSTGRES_HOST="${POSTGRES_HOST:-}"
REDIS_HOST="${REDIS_HOST:-}"

if [[ -f "$JSON_FILE" ]]; then
    log_info "Loading infrastructure details from ${JSON_FILE}..."
    RESOURCE_GROUP=$(jq -r '.RESOURCE_GROUP // .TF_BACKEND_RG' "$JSON_FILE")
    AKS_CLUSTER_NAME=$(jq -r '.AKS_CLUSTER_NAME // empty' "$JSON_FILE")
    ACR_NAME=$(jq -r '.ACR_NAME // empty' "$JSON_FILE")
    KEYVAULT_NAME=$(jq -r '.KEYVAULT_NAME // empty' "$JSON_FILE")
    POSTGRES_HOST=$(jq -r '.POSTGRES_HOST // empty' "$JSON_FILE")
    REDIS_HOST=$(jq -r '.REDIS_HOST // empty' "$JSON_FILE")
fi

# Fallback defaults if still empty
PROJECT_NAME="${EITOAP_PROJECT_NAME:-eitoap}"
ENVIRONMENT="${EITOAP_ENVIRONMENT:-dev}"
RESOURCE_GROUP="${RESOURCE_GROUP:-${PROJECT_NAME}-${ENVIRONMENT}-rg}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-enterprise-${ENVIRONMENT}-aks}"

PASS_COUNT=0
FAIL_COUNT=0

report_result() {
    local check_name="$1"
    local status="$2"
    local details="${3:-}"
    
    if [ "$status" = "PASS" ]; then
        echo -e "[ ${GREEN}${BOLD}PASS${NC} ] $check_name ${details:+($details)}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "[ ${RED}${BOLD}FAIL${NC} ] $check_name ${details:+($details)}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# 1. Verify Infrastructure
log_info "1. Verifying Azure Resource Provisioning..."

# Resource Group
if az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    report_result "Resource Group '$RESOURCE_GROUP'" "PASS"
else
    report_result "Resource Group '$RESOURCE_GROUP'" "FAIL" "Not found"
fi

# AKS Cluster
if [[ -n "$AKS_CLUSTER_NAME" ]] && az aks show --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" >/dev/null 2>&1; then
    report_result "AKS Cluster '$AKS_CLUSTER_NAME'" "PASS"
else
    report_result "AKS Cluster" "FAIL" "Not found or AKS_CLUSTER_NAME is empty"
fi

# ACR
if [[ -n "$ACR_NAME" ]] && az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
    report_result "Container Registry '$ACR_NAME'" "PASS"
else
    report_result "Container Registry" "FAIL" "Not found or ACR_NAME is empty"
fi

# Key Vault
if [[ -n "$KEYVAULT_NAME" ]] && az keyvault show --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
    report_result "Key Vault '$KEYVAULT_NAME'" "PASS"
else
    report_result "Key Vault" "FAIL" "Not found or KEYVAULT_NAME is empty"
fi

# PostgreSQL Flexible Server
if [[ -n "$POSTGRES_HOST" ]]; then
    # Host is servername.postgres.database.azure.com, extract servername
    server_name=$(echo "$POSTGRES_HOST" | cut -d. -f1)
    # Flexible servers can be in a different RG/Location as configured in TF, let's search subscription if not in resource group
    if az postgres flexible-server show --name "$server_name" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
        report_result "PostgreSQL Server '$server_name'" "PASS"
    else
        # Try checking across the subscription
        if az postgres flexible-server list --query "[?name=='$server_name'] | length(@)" -o tsv 2>/dev/null | grep -q "1"; then
            report_result "PostgreSQL Server '$server_name'" "PASS" "Found in subscription"
        else
            report_result "PostgreSQL Server '$server_name'" "FAIL" "Not found"
        fi
    fi
else
    report_result "PostgreSQL Server" "FAIL" "Host name not found in configuration"
fi

# Redis Cache
if [[ -n "$REDIS_HOST" ]]; then
    redis_name=$(echo "$REDIS_HOST" | cut -d. -f1)
    if az redis show --name "$redis_name" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
        report_result "Redis Cache '$redis_name'" "PASS"
    else
        report_result "Redis Cache '$redis_name'" "FAIL" "Not found"
    fi
else
    report_result "Redis Cache" "FAIL" "Host name not found in configuration"
fi


# 2. Verify Kubernetes Resources
log_info "2. Verifying Kubernetes Components..."

# Kubeconfig context check
if ! kubectl cluster-info >/dev/null 2>&1; then
    log_info "Attempting to retrieve AKS cluster credentials..."
    if ! az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER_NAME" --overwrite-existing >/dev/null 2>&1; then
        report_result "Kubernetes Connectivity" "FAIL" "Unable to obtain kubeconfig credentials"
        exit 1
    fi
fi
report_result "Kubernetes API Connectivity" "PASS"

# Nodes status
READY_NODES=$(kubectl get nodes -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -o "True" | wc -l || echo "0")
if [ "$READY_NODES" -gt 0 ]; then
    report_result "AKS Worker Nodes" "PASS" "$READY_NODES node(s) ready"
else
    report_result "AKS Worker Nodes" "FAIL" "No ready nodes found"
fi

# Namespaces verification
declare -a namespaces=("backend" "frontend" "database")
for ns in "${namespaces[@]}"; do
    if kubectl get ns "$ns" >/dev/null 2>&1; then
        report_result "Namespace: $ns" "PASS"
    else
        report_result "Namespace: $ns" "FAIL" "Not found"
    fi
done

# Ingress controller check
if kubectl get svc -n ingress-nginx 2>/dev/null | grep -q "ingress-nginx"; then
    report_result "Ingress Controller" "PASS" "ingress-nginx service exists"
elif kubectl get pods -A -l app.kubernetes.io/name=ingress-nginx 2>/dev/null | grep -q "ingress-nginx"; then
    report_result "Ingress Controller" "PASS" "ingress-nginx pods exist"
else
    report_result "Ingress Controller" "FAIL" "No ingress controller found in cluster"
fi

# cert-manager check
if kubectl get pods -n cert-manager 2>/dev/null | grep -q "cert-manager"; then
    report_result "cert-manager" "PASS" "cert-manager pods are running"
else
    report_result "cert-manager" "FAIL" "cert-manager not detected (optional)"
fi


# 3. Verify Deployments and Pod Health
log_info "3. Verifying Pods and Deployments Health..."

# Backend Deployment
if kubectl rollout status deployment/backend-deployment -n backend --timeout=5s >/dev/null 2>&1; then
    report_result "Backend Rollout Status" "PASS"
else
    report_result "Backend Rollout Status" "FAIL" "Deployment failed or timed out"
fi

# Frontend Deployment
if kubectl rollout status deployment/frontend-deployment -n frontend --timeout=5s >/dev/null 2>&1; then
    report_result "Frontend Rollout Status" "PASS"
else
    report_result "Frontend Rollout Status" "FAIL" "Deployment failed or timed out"
fi

# Check for failing pods
FAILED_PODS=$(kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded -o name | wc -l || echo "0")
if [ "$FAILED_PODS" -eq 0 ]; then
    report_result "Cluster Pod Health" "PASS" "0 failing/pending pods"
else
    report_result "Cluster Pod Health" "FAIL" "$FAILED_PODS non-running pods found"
fi


# 4. Verify Connectivity and Endpoint Health
log_info "4. Testing End-to-End Application Health & Connectivity..."

# Find a running backend or frontend pod to run curl checks from inside the cluster
BACKEND_POD=$(kubectl get pods -n backend -l app.kubernetes.io/name=backend -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [[ -n "$BACKEND_POD" ]]; then
    # Test Readiness endpoint (checks DB and Redis connectivity)
    log_info "Running backend readiness check from inside backend pod..."
    READINESS_RESP=$(kubectl exec -n backend pod/$BACKEND_POD -- curl -s http://localhost:8000/api/v1/readiness || echo "failed")
    
    if [[ "$READINESS_RESP" == *"\"status\":\"ready\""* ]]; then
        report_result "Backend Health Endpoint (/api/v1/readiness)" "PASS"
        
        # Redis Connectivity Check
        if [[ "$READINESS_RESP" == *"\"redis\":\"connected\""* ]]; then
            report_result "Redis Connectivity" "PASS"
        else
            report_result "Redis Connectivity" "FAIL" "Backend reports Redis is offline"
        fi
        
        # PostgreSQL Connectivity Check
        if [[ "$READINESS_RESP" == *"\"database\":\"connected\""* ]]; then
            report_result "PostgreSQL Connectivity" "PASS"
        else
            report_result "PostgreSQL Connectivity" "FAIL" "Backend reports PostgreSQL is offline"
        fi
    else
        report_result "Backend Health Endpoint (/api/v1/readiness)" "FAIL" "Response: $READINESS_RESP"
        report_result "Redis Connectivity" "FAIL" "Unable to check due to backend failures"
        report_result "PostgreSQL Connectivity" "FAIL" "Unable to check due to backend failures"
    fi
else
    report_result "Backend Health Endpoint" "FAIL" "No running backend pods found to execute tests from"
    report_result "Redis Connectivity" "FAIL" "Backend pod not found"
    report_result "PostgreSQL Connectivity" "FAIL" "Backend pod not found"
fi

# Frontend Availability Check (Ingress IP or service)
FRONTEND_SVC_IP=$(kubectl get svc frontend-service -n frontend -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
if [[ -n "$FRONTEND_SVC_IP" ]]; then
    # Test frontend service internally
    if [[ -n "$BACKEND_POD" ]]; then
        FRONTEND_HTTP_CODE=$(kubectl exec -n backend pod/$BACKEND_POD -- curl -s -o /dev/null -w "%{http_code}" http://frontend-service.frontend.svc.cluster.local || echo "000")
        if [ "$FRONTEND_HTTP_CODE" -eq 200 ] || [ "$FRONTEND_HTTP_CODE" -eq 304 ]; then
            report_result "Frontend Internal Availability" "PASS" "Status $FRONTEND_HTTP_CODE"
        else
            report_result "Frontend Internal Availability" "FAIL" "Status $FRONTEND_HTTP_CODE"
        fi
    else
        report_result "Frontend Internal Availability" "FAIL" "Cannot test (no backend pod)"
    fi
else
    report_result "Frontend Internal Availability" "FAIL" "frontend-service not found"
fi

# Ingress Controller Public IP
INGRESS_IP=$(kubectl get ingress -A -o jsonpath='{.items[*].status.loadBalancer.ingress[*].ip}' 2>/dev/null || echo "")
if [[ -n "$INGRESS_IP" ]]; then
    report_result "Ingress Controller External IP" "PASS" "LoadBalancer IP: $INGRESS_IP"
else
    report_result "Ingress Controller External IP" "FAIL" "LoadBalancer IP pending / not assigned"
fi

echo "========================================================="
log_info "Verification Summary:"
log_success "  Passed Checks: $PASS_COUNT"
if [ "$FAIL_COUNT" -gt 0 ]; then
    log_error "  Failed Checks: $FAIL_COUNT"
    log_error "VERIFICATION STATUS: FAIL"
    exit 1
else
    log_success "VERIFICATION STATUS: PASS"
    exit 0
fi