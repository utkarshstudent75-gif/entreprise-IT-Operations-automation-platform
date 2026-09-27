#!/usr/bin/env bash

# Source common script
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
source "${SCRIPT_DIR}/_common.sh"

set -Eeuo pipefail

log_info "Configuring GitHub Repository Secrets..."

# Load output JSON if it exists
JSON_FILE="${SCRIPT_DIR}/.bootstrap-output.json"
declare -A secrets

if [[ -f "$JSON_FILE" ]]; then
    log_info "Found bootstrap outputs in ${JSON_FILE}. Loading values..."
    # Read keys from JSON
    while IFS= read -r key; do
        val=$(jq -r ".[\"$key\"]" "$JSON_FILE")
        if [[ "$val" != "null" && -n "$val" ]]; then
            secrets[$key]="$val"
        fi
    done < <(jq -r 'keys[]' "$JSON_FILE")
fi

# Fallback/override with environment variables
declare -a var_names=(
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "AZURE_SUBSCRIPTION_ID"
    "AZURE_TENANT_ID"
    "ACR_NAME"
    "AKS_CLUSTER_NAME"
    "RESOURCE_GROUP"
    "POSTGRES_HOST"
    "REDIS_HOST"
    "KEYVAULT_NAME"
)

for var in "${var_names[@]}"; do
    # If set in environment, override JSON
    if [[ -n "${!var:-}" ]]; then
        secrets[$var]="${!var}"
    fi
done

# Verify we have at least the Azure client ID (required for OIDC auth in CI)
if [[ -z "${secrets[AZURE_CLIENT_ID]:-}" ]]; then
    log_warn "Azure Service Principal client ID (AZURE_CLIENT_ID) not found in bootstrap output or environment."
    log_warn "Please ensure you ran bootstrap.sh first."
fi

# Warn (but do not block) if client secret is missing — CI uses OIDC federated identity,
# so AZURE_CLIENT_SECRET is not required for the GitHub Actions pipeline
if [[ -z "${secrets[AZURE_CLIENT_SECRET]:-}" ]]; then
    log_info "AZURE_CLIENT_SECRET is not set. CI uses OIDC federated identity; this is only needed for local tooling."
fi

# Check if gh CLI is available and authenticated
GH_AVAILABLE=false
if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then
        GH_AVAILABLE=true
    else
        log_warn "GitHub CLI (gh) is installed but not authenticated. Run 'gh auth login' to authenticate."
    fi
else
    log_warn "GitHub CLI (gh) is not installed."
fi

if [ "$GH_AVAILABLE" = true ]; then
    log_info "GitHub CLI detected and authenticated. Setting repository secrets..."
    
    for key in "${!secrets[@]}"; do
        val="${secrets[$key]}"
        if [[ -n "$val" ]]; then
            # Mask output to avoid printing secrets in console
            masked_val=$(mask_secret "$val")
            log_info "Setting secret: $key = $masked_val"
            echo -n "$val" | gh secret set "$key" 2>/dev/null || {
                log_error "Failed to set GitHub secret '$key'."
            }
        fi
    done
    log_success "All available secrets configured in GitHub repository!"
else
    # Write to file
    SECRETS_TXT="${SCRIPT_DIR}/github-secrets.txt"
    log_warn "Writing secrets to local file: $SECRETS_TXT (This file is git-ignored)"
    
    cat <<EOF > "$SECRETS_TXT"
===================================================================
GitHub Secrets Configuration (Manual Copy Required)
===================================================================
Copy and paste the following key-value pairs as Actions Secrets
in your GitHub repository (Settings -> Secrets and variables -> Actions).

EOF
    
    for key in "${var_names[@]}"; do
        val="${secrets[$key]:-}"
        if [[ -n "$val" ]]; then
            echo "$key=$val" >> "$SECRETS_TXT"
            masked_val=$(mask_secret "$val")
            echo "$key=$masked_val"
        else
            echo "$key=(Not configured - please set manually)" >> "$SECRETS_TXT"
            echo "$key=(Not configured)"
        fi
    done
    
    echo -e "\n===================================================================" >> "$SECRETS_TXT"
    log_success "Secrets exported successfully. Please see $SECRETS_TXT"
fi