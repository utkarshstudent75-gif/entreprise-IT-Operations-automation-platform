#!/usr/bin/env bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Logger functions
log_info() {
    echo -e "${BLUE}${BOLD}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}${BOLD}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}${BOLD}[ERROR]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}${BOLD}[SUCCESS]${NC} $1"
}

# Dependency checker with installation guidance
require_tool() {
    local tool_name="$1"
    local install_guidance="$2"
    
    if ! command -v "$tool_name" >/dev/null 2>&1; then
        log_warn "Missing required dependency: ${BOLD}$tool_name${NC}"
        echo -e "  To install: $install_guidance"
        return 1
    fi
    log_info "Verified dependency: ${BOLD}$tool_name${NC}"
    return 0
}

# Interactive confirmation prompt
confirm_action() {
    local prompt_msg="$1"
    local default_choice="${2:-N}"
    local yn_options="[y/N]"
    
    if [[ "$default_choice" =~ ^[Yy]$ ]]; then
        yn_options="[Y/n]"
    fi
    
    echo -ne "${YELLOW}${BOLD}$prompt_msg $yn_options: ${NC}"
    read -r response
    
    # If empty response, use default
    if [[ -z "$response" ]]; then
        response="$default_choice"
    fi
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Mask sensitive value for displaying
mask_secret() {
    local secret="$1"
    local len=${#secret}
    if [ "$len" -le 8 ]; then
        echo "********"
    else
        echo "${secret:0:4}...${secret: -4}"
    fi
}
