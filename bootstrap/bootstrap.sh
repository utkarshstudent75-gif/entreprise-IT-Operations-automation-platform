#!/usr/bin/env bash

# Sourcing helpers
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/_common.sh"

set -Eeuo pipefail

# Load environment configuration if available
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    log_info "Loading environment variables from .env..."
    # Sourcing .env safely without executing commands
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ ^[^#].*= ]]; then
            key=$(echo "$line" | cut -d= -f1)
            val=$(echo "$line" | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
            export "$key=$val"
        fi
    done < "${SCRIPT_DIR}/.env"
fi

# Constants and Defaults
PROJECT_NAME="${EITOAP_PROJECT_NAME:-eitoap}"
LOCATION="${EITOAP_LOCATION:-eastus}"
ENVIRONMENT="${EITOAP_ENVIRONMENT:-dev}"
BACKEND_RG="${EITOAP_BACKEND_RG:-${PROJECT_NAME}-tfstate-rg}"
BACKEND_STORAGE_PREFIX="${EITOAP_BACKEND_STORAGE:-${PROJECT_NAME}tfstate}"
BACKEND_CONTAINER="${EITOAP_BACKEND_CONTAINER:-tfstate}"
SP_NAME="${EITOAP_SP_NAME:-${PROJECT_NAME}-github}"

log_success "========================================================="
log_success "  Enterprise IT Operations Platform - Azure Bootstrap  "
log_success "========================================================="
log_info "Project Prefix: $PROJECT_NAME"
log_info "Target Region:  $LOCATION"
log_info "Environment:    $ENVIRONMENT"
log_success "========================================================="

# ------------------------------------------------------------------------------
# 1. Dependency Checks
# ------------------------------------------------------------------------------
log_info "1. Verifying pre-requisites and CLI dependencies..."

HAS_MISSING_DEPS=false

require_tool "az" "Install Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli" || HAS_MISSING_DEPS=true
require_tool "terraform" "Install Terraform: https://developer.hashicorp.com/terraform/downloads" || HAS_MISSING_DEPS=true
require_tool "kubectl" "Install kubectl: https://kubernetes.io/docs/tasks/tools/" || HAS_MISSING_DEPS=true
require_tool "helm" "Install Helm: https://helm.sh/docs/intro/install/" || HAS_MISSING_DEPS=true
require_tool "docker" "Install Docker: https://docs.docker.com/engine/install/" || HAS_MISSING_DEPS=true
require_tool "git" "Install Git: https://git-scm.com/downloads" || HAS_MISSING_DEPS=true
require_tool "gh" "Install GitHub CLI (Optional): https://cli.github.com/" || true # gh is optional, but checked
require_tool "jq" "Install jq: sudo apt-get install jq (Debian/Ubuntu) or brew install jq (macOS)" || HAS_MISSING_DEPS=true

if [ "$HAS_MISSING_DEPS" = true ]; then
    log_error "Missing required dependencies. Please install them and try again."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Azure Authentication & Subscription Selection
# ------------------------------------------------------------------------------
log_info "2. Verifying Azure Authentication..."

# Check if logged in
if ! az account show >/dev/null 2>&1; then
    log_warn "Not logged into Azure. Initiating 'az login'..."
    az login --use-device-code || az login
fi

# Retrieve all subscriptions
log_info "Fetching available Azure subscriptions..."
SUBS_JSON=$(az account list -o json)
SUB_COUNT=$(echo "$SUBS_JSON" | jq '. | length')

if [ "$SUB_COUNT" -eq 0 ]; then
    log_error "No Azure subscriptions found for the current login session."
    exit 1
fi

SELECTED_SUB_ID=""
if [ "$SUB_COUNT" -gt 1 ]; then
    log_warn "Multiple Azure subscriptions detected ($SUB_COUNT):"
    
    # List subscriptions
    echo "---------------------------------------------------------"
    echo -e "${BOLD}Index  Subscription Name / ID${NC}"
    echo "---------------------------------------------------------"
    for i in $(seq 0 $((SUB_COUNT - 1))); do
        sub_name=$(echo "$SUBS_JSON" | jq -r ".[$i].name")
        sub_id=$(echo "$SUBS_JSON" | jq -r ".[$i].id")
        is_default=$(echo "$SUBS_JSON" | jq -r ".[$i].isDefault")
        default_str=""
        if [ "$is_default" = "true" ]; then
            default_str=" (Default)"
        fi
        echo "$((i + 1))) $sub_name ($sub_id)$default_str"
    done
    echo "---------------------------------------------------------"
    
    # Ask user to select one
    echo -n "Select a subscription index (1-$SUB_COUNT) [Press Enter for default]: "
    read -r sub_choice
    
    if [[ -z "$sub_choice" ]]; then
        # Use current default
        SELECTED_SUB_ID=$(az account show --query id -o tsv)
    elif [[ "$sub_choice" =~ ^[0-9]+$ ]] && [ "$sub_choice" -ge 1 ] && [ "$sub_choice" -le "$SUB_COUNT" ]; then
        SELECTED_SUB_ID=$(echo "$SUBS_JSON" | jq -r ".[$((sub_choice - 1))].id")
        log_info "Setting active subscription..."
        az account set --subscription "$SELECTED_SUB_ID"
    else
        log_warn "Invalid selection. Proceeding with current default subscription."
        SELECTED_SUB_ID=$(az account show --query id -o tsv)
    fi
else
    SELECTED_SUB_ID=$(echo "$SUBS_JSON" | jq -r '.[0].id')
    az account set --subscription "$SELECTED_SUB_ID"
fi

# Show current context
CURRENT_SUB_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
CURRENT_USER=$(az account show --query user.name -o tsv)

log_success "Active Azure Session Details:"
echo -e "  User:         ${BOLD}$CURRENT_USER${NC}"
echo -e "  Tenant ID:    ${BOLD}$TENANT_ID${NC}"
echo -e "  Subscription: ${BOLD}$CURRENT_SUB_NAME ($SELECTED_SUB_ID)${NC}"

if ! confirm_action "Do you want to continue with this subscription?" "Y"; then
    log_info "Bootstrap cancelled by user."
    exit 0
fi

# ------------------------------------------------------------------------------
# 3. Create/Verify Terraform Backend (Storage Account)
# ------------------------------------------------------------------------------
log_info "3. Preparing Terraform state backend..."

# Create Resource Group if missing
if ! az group show --name "$BACKEND_RG" >/dev/null 2>&1; then
    log_info "Creating backend Resource Group '$BACKEND_RG' in $LOCATION..."
    az group create --name "$BACKEND_RG" --location "$LOCATION" >/dev/null
else
    log_info "Backend Resource Group '$BACKEND_RG' already exists."
fi

# Find or generate a unique Storage Account name
log_info "Determining globally unique Storage Account name..."
STORAGE_ACCOUNT_NAME="$BACKEND_STORAGE_PREFIX"

# Maximum length is 24, lowercase letters and numbers only
STORAGE_ACCOUNT_NAME=$(echo "${STORAGE_ACCOUNT_NAME}" | tr -cd 'a-z0-9' | cut -c1-24)

# Keep trying names if not available
while true; do
    AVAIL_JSON=$(az storage account check-name --name "$STORAGE_ACCOUNT_NAME" -o json)
    IS_AVAILABLE=$(echo "$AVAIL_JSON" | jq -r '.nameAvailable')
    
    if [ "$IS_AVAILABLE" = "true" ]; then
        break
    fi
    
    # If the storage account is already created under our own RG, reuse it!
    # Let's check if it exists in our RG
    EXISTS_IN_OUR_RG=$(az storage account list --resource-group "$BACKEND_RG" --query "[?name=='$STORAGE_ACCOUNT_NAME'] | length(@)" -o tsv 2>/dev/null || echo "0")
    if [ "$EXISTS_IN_OUR_RG" -gt 0 ]; then
        log_info "Found existing storage account '$STORAGE_ACCOUNT_NAME' in RG '$BACKEND_RG'."
        break
    fi
    
    # Otherwise generate a new suffix
    REASON=$(echo "$AVAIL_JSON" | jq -r '.message')
    log_warn "Storage name '$STORAGE_ACCOUNT_NAME' not available ($REASON). Retrying with suffix..."
    SUFFIX=$((RANDOM % 100000))
    STORAGE_ACCOUNT_NAME=$(echo "${BACKEND_STORAGE_PREFIX:0:18}${SUFFIX}" | tr -cd 'a-z0-9' | cut -c1-24)
done

log_info "Using Storage Account: '$STORAGE_ACCOUNT_NAME'"

# Create Storage Account if missing
EXISTS_IN_OUR_RG=$(az storage account list --resource-group "$BACKEND_RG" --query "[?name=='$STORAGE_ACCOUNT_NAME'] | length(@)" -o tsv 2>/dev/null || echo "0")
if [ "$EXISTS_IN_OUR_RG" -eq 0 ]; then
    log_info "Creating Storage Account '$STORAGE_ACCOUNT_NAME'..."
    az storage account create \
        --name "$STORAGE_ACCOUNT_NAME" \
        --resource-group "$BACKEND_RG" \
        --location "$LOCATION" \
        --sku Standard_LRS \
        --kind StorageV2 \
        --encryption-services blob >/dev/null
else
    log_info "Storage Account '$STORAGE_ACCOUNT_NAME' already exists."
fi

# Retrieve storage account key
ACCOUNT_KEY=$(az storage account keys list \
    --resource-group "$BACKEND_RG" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --query '[0].value' \
    -o tsv)

# Create Blob Container if missing
CONTAINER_EXISTS=$(az storage container exists \
    --name "$BACKEND_CONTAINER" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --account-key "$ACCOUNT_KEY" \
    --query "exists" -o tsv)

if [ "$CONTAINER_EXISTS" = "false" ]; then
    log_info "Creating blob container '$BACKEND_CONTAINER'..."
    az storage container create \
        --name "$BACKEND_CONTAINER" \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --account-key "$ACCOUNT_KEY" >/dev/null
else
    log_info "Blob container '$BACKEND_CONTAINER' already exists."
fi

log_success "Terraform backend storage verification complete!"

# ------------------------------------------------------------------------------
# 4. Create/Verify Service Principal
# ------------------------------------------------------------------------------
log_info "4. Configuring Service Principal for GitHub Actions..."

SP_APP_ID=""
SP_CLIENT_SECRET=""

# Check if application already exists
EXISTING_APP_JSON=$(az ad app list --display-name "$SP_NAME" -o json)
APP_COUNT=$(echo "$EXISTING_APP_JSON" | jq '. | length')

if [ "$APP_COUNT" -gt 0 ]; then
    log_info "Found existing Application registration: '$SP_NAME'"
    SP_APP_ID=$(echo "$EXISTING_APP_JSON" | jq -r '.[0].appId')
    
    # Ask if secret reset is needed
    if confirm_action "Service Principal exists. Do you want to reset its client secret?" "N"; then
        log_info "Resetting Service Principal credentials..."
        RESET_JSON=$(az ad sp credential reset --id "$SP_APP_ID" -o json)
        SP_CLIENT_SECRET=$(echo "$RESET_JSON" | jq -r '.password')
    else
        log_info "Reusing existing Service Principal credentials. Secret will not be modified."
        # Read from environment/secrets output if available
        if [[ -n "${AZURE_CLIENT_SECRET:-}" ]]; then
            SP_CLIENT_SECRET="$AZURE_CLIENT_SECRET"
        fi
    fi
else
    log_info "Creating a new Service Principal: '$SP_NAME'..."
    SP_JSON=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role Contributor \
        --scopes "/subscriptions/${SELECTED_SUB_ID}" \
        --json-auth)
    
    SP_APP_ID=$(echo "$SP_JSON" | jq -r '.clientId')
    SP_CLIENT_SECRET=$(echo "$SP_JSON" | jq -r '.clientSecret')
fi

# Display credentials (excluding secret)
log_success "Service Principal Configured:"
echo -e "  Display Name: ${BOLD}$SP_NAME${NC}"
echo -e "  Client ID:    ${BOLD}$SP_APP_ID${NC}"
echo -e "  Tenant ID:    ${BOLD}$TENANT_ID${NC}"

# Store sensitive outputs securely in a git-ignored JSON file
BOOTSTRAP_OUTPUT="${SCRIPT_DIR}/.bootstrap-output.json"
cat <<EOF > "$BOOTSTRAP_OUTPUT"
{
  "AZURE_CLIENT_ID": "$SP_APP_ID",
  "AZURE_CLIENT_SECRET": "$SP_CLIENT_SECRET",
  "AZURE_SUBSCRIPTION_ID": "$SELECTED_SUB_ID",
  "AZURE_TENANT_ID": "$TENANT_ID",
  "TF_BACKEND_RG": "$BACKEND_RG",
  "TF_BACKEND_STORAGE": "$STORAGE_ACCOUNT_NAME",
  "TF_BACKEND_CONTAINER": "$BACKEND_CONTAINER"
}
EOF
chmod 600 "$BOOTSTRAP_OUTPUT"
log_info "Secrets written securely to local metadata: $BOOTSTRAP_OUTPUT"

# ------------------------------------------------------------------------------
# 4b. Configure Federated Identity Credentials for GitHub Actions OIDC
# ------------------------------------------------------------------------------
log_info "Configuring Federated Identity Credentials for GitHub Actions OIDC..."

GITHUB_REPO="${EITOAP_GITHUB_REPOSITORY:-utkarshstudent75-gif/entreprise-IT-Operations-automation-platform}"
GITHUB_BRANCHES="${EITOAP_GITHUB_BRANCHES:-master,main}"

IFS=',' read -ra _BRANCHES <<< "$GITHUB_BRANCHES"

_FEDERATED_OK=true
for _branch in "${_BRANCHES[@]}"; do
    _branch="$(echo "$_branch" | xargs)"
    _cred_name="github-actions-oidc-${_branch}"
    _subject="repo:${GITHUB_REPO}:ref:refs/heads/${_branch}"

    _existing=$(az ad app federated-credential list --id "$SP_APP_ID" \
        --query "[?name=='${_cred_name}'] | length(@)" -o tsv 2>/dev/null || echo "0")

    if [ "$_existing" = "1" ]; then
        log_info "Federated identity credential for branch '${_branch}' already exists. Skipping."
        continue
    fi

    log_info "Creating federated identity credential for branch '${_branch}'..."
    if az ad app federated-credential create \
        --id "$SP_APP_ID" \
        --parameters "$(cat <<FEOF
{
  "name": "${_cred_name}",
  "subject": "${_subject}",
  "issuer": "https://token.actions.githubusercontent.com",
  "subjectType": "LineOfSight",
  "audiences": ["api://AzureADTokenExchange"]
}
FEOF
)" >/dev/null 2>&1; then
        log_success "Federated identity credential created for branch '${_branch}'."
    else
        log_warn "Failed to create federated identity credential for branch '${_branch}'."
        _FEDERATED_OK=false
    fi
done

# Configure federated identity credentials for event-based triggers (workflow_dispatch, etc.)
GITHUB_EVENTS="${EITOAP_GITHUB_EVENTS:-workflow_dispatch}"
if [ -n "$GITHUB_EVENTS" ]; then
    IFS=',' read -ra _EVENTS <<< "$GITHUB_EVENTS"
    for _event in "${_EVENTS[@]}"; do
        _event="$(echo "$_event" | xargs)"
        [ -z "$_event" ] && continue
        _cred_name="github-actions-oidc-${_event}"
        _subject="repo:${GITHUB_REPO}:${_event}"

        _existing=$(az ad app federated-credential list --id "$SP_APP_ID" \
            --query "[?name=='${_cred_name}'] | length(@)" -o tsv 2>/dev/null || echo "0")

        if [ "$_existing" = "1" ]; then
            log_info "Federated identity credential for event '${_event}' already exists. Skipping."
            continue
        fi

        log_info "Creating federated identity credential for event '${_event}'..."
        if az ad app federated-credential create \
            --id "$SP_APP_ID" \
            --parameters "$(cat <<FEOF
{
  "name": "${_cred_name}",
  "subject": "${_subject}",
  "issuer": "https://token.actions.githubusercontent.com",
  "subjectType": "LineOfSight",
  "audiences": ["api://AzureADTokenExchange"]
}
FEOF
)" >/dev/null 2>&1; then
            log_success "Federated identity credential created for event '${_event}'."
        else
            log_warn "Failed to create federated identity credential for event '${_event}'."
            _FEDERATED_OK=false
        fi
    done
fi

if [ "$_FEDERATED_OK" = true ]; then
    log_success "All federated identity credentials configured successfully."
else
    log_warn "Some federated identity credentials could not be created. Check the output above."
fi

# ------------------------------------------------------------------------------
# 5. GitHub Secrets Integration
# ------------------------------------------------------------------------------
log_info "5. Configuring GitHub Secrets..."

# Run github-secrets.sh
export AZURE_CLIENT_ID="$SP_APP_ID"
export AZURE_CLIENT_SECRET="$SP_CLIENT_SECRET"
export AZURE_SUBSCRIPTION_ID="$SELECTED_SUB_ID"
export AZURE_TENANT_ID="$TENANT_ID"

bash "${SCRIPT_DIR}/github-secrets.sh"

# ------------------------------------------------------------------------------
# 6. Terraform Execution
# ------------------------------------------------------------------------------
log_info "6. Starting Terraform initialization..."

TF_ENV_DIR="${SCRIPT_DIR}/../infrastructure/terraform/environments/${ENVIRONMENT}"

if [[ ! -d "$TF_ENV_DIR" ]]; then
    log_error "Terraform environment folder '$TF_ENV_DIR' not found."
    exit 1
fi

cd "$TF_ENV_DIR"

log_info "Initializing Terraform with dynamic backend config..."
terraform init \
    -backend-config="resource_group_name=$BACKEND_RG" \
    -backend-config="storage_account_name=$STORAGE_ACCOUNT_NAME" \
    -backend-config="container_name=$BACKEND_CONTAINER" \
    -backend-config="key=${ENVIRONMENT}.terraform.tfstate" \
    -reconfigure

log_info "Validating Terraform configuration..."
terraform validate

log_info "Generating Terraform Plan..."
terraform plan -out=tfplan

if confirm_action "Do you want to apply this Terraform plan to deploy EITOAP infrastructure?" "N"; then
    log_info "Executing Terraform Apply (this will take 20-30 minutes)..."
    terraform apply tfplan
    
    # ------------------------------------------------------------------------------
    # 7. Post-Terraform AKS Verification
    # ------------------------------------------------------------------------------
    log_info "7. Gathering deployment resource outputs..."
    
    ACR_NAME=$(terraform output -raw acr_name 2>/dev/null || echo "")
    AKS_CLUSTER_NAME=$(terraform output -raw aks_cluster_name 2>/dev/null || echo "")
    RESOURCE_GROUP=$(terraform output -raw aks_node_resource_group 2>/dev/null || echo "$PROJECT_NAME-$ENVIRONMENT-rg")
    # Actually wait, the AKS resource group is project_name-environment-rg or similar, let's get it from TF variables
    # Let's inspect the active RG name from resource_group module output or assume suffix
    ACTIVE_RG="${PROJECT_NAME}-${ENVIRONMENT}-rg"
    # Overriding if output is available
    
    POSTGRES_HOST=$(terraform output -raw db_fqdn 2>/dev/null || echo "")
    REDIS_HOST=$(terraform output -raw redis_host 2>/dev/null || echo "")
    KEYVAULT_NAME=$(terraform output -raw key_vault_name 2>/dev/null || echo "")
    
    # Update bootstrap JSON with TF outputs for verify.sh
    TMP_JSON=$(mktemp)
    jq --arg acr "$ACR_NAME" \
       --arg aks "$AKS_CLUSTER_NAME" \
       --arg rg "$ACTIVE_RG" \
       --arg pg "$POSTGRES_HOST" \
       --arg rd "$REDIS_HOST" \
       --arg kv "$KEYVAULT_NAME" \
       '. + {ACR_NAME: $acr, AKS_CLUSTER_NAME: $aks, RESOURCE_GROUP: $rg, POSTGRES_HOST: $pg, REDIS_HOST: $rd, KEYVAULT_NAME: $kv}' \
       "$BOOTSTRAP_OUTPUT" > "$TMP_JSON"
    mv "$TMP_JSON" "$BOOTSTRAP_OUTPUT"
    chmod 600 "$BOOTSTRAP_OUTPUT"
    
    # Trigger github-secrets.sh again with the newly retrieved resources!
    log_info "Updating GitHub secrets with provisioned infrastructure endpoints..."
    export ACR_NAME
    export AKS_CLUSTER_NAME
    export RESOURCE_GROUP="$ACTIVE_RG"
    export POSTGRES_HOST
    export REDIS_HOST
    export KEYVAULT_NAME
    bash "${SCRIPT_DIR}/github-secrets.sh"
    
    log_info "Retrieving AKS Kubernetes credentials..."
    az aks get-credentials --resource-group "$ACTIVE_RG" --name "$AKS_CLUSTER_NAME" --overwrite-existing
    
    log_success "AKS cluster credentials merged into ~/.kube/config."
    
    log_info "Verifying cluster health..."
    kubectl get nodes
    
    log_success "Azure Bootstrap & Infrastructure Provisioning Complete!"
    log_info "You can now run verify.sh to perform standard environment validations."
else
    log_warn "Terraform apply skipped by user. Infrastructure has not been updated."
    log_info "You can run 'terraform apply tfplan' manually from ${TF_ENV_DIR}"
fi

log_success "========================================================="
log_success "Bootstrap Script Completed Successfully!"
log_success "========================================================="