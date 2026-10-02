#!/usr/bin/env bash
set -euo pipefail

# Creates a new immutable Foundry agent version while preserving the current
# model and instructions and attaching the function schemas used by the backend.
# Run in Azure Cloud Shell after `az login`.

PROJECT_ENDPOINT="${FOUNDRY_PROJECT_ENDPOINT:-https://eitoap-ops-foundry-2026.services.ai.azure.com/api/projects/eitoap-ops-assistant}"
AGENT_NAME="${FOUNDRY_AGENT_NAME:-eitoap-ops-assistant}"
API_VERSION="v1"

command -v az >/dev/null || { echo 'Azure CLI (az) is required.' >&2; exit 1; }
command -v jq >/dev/null || { echo 'jq is required.' >&2; exit 1; }

TOKEN="$(az account get-access-token --scope "https://ai.azure.com/.default" --query accessToken -o tsv)"
[ -n "$TOKEN" ] || { echo "Could not get a Foundry access token. Run az login." >&2; exit 1; }

TOOLS='[
  {"type":"function","name":"get_azure_resource_inventory","description":"List non-sensitive Azure resource metadata across the configured subscription. Does not read Terraform state contents or secret values.","parameters":{"type":"object","properties":{},"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_azure_resource_health","description":"Get reported Azure Resource Health states for resources in the configured subscription. Missing health results are not proof that resources are healthy.","parameters":{"type":"object","properties":{},"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_azure_resource_metrics","description":"Read the most recent hour of an available Azure Monitor metric for one exact resource ID returned by the resource inventory tool.","parameters":{"type":"object","properties":{"resource_id":{"type":"string","description":"Exact Azure resource ID from the configured inventory."},"metric_name":{"type":"string","description":"Exact Azure Monitor metric name supported by the resource."}},"required":["resource_id","metric_name"],"additionalProperties":false},"strict":true},
  {"type":"function","name":"get_subscription_log_workspaces","description":"Discover Log Analytics workspace IDs in the configured Azure subscription.","parameters":{"type":"object","properties":{},"additionalProperties":false},"strict":true},
  {"type":"function","name":"query_azure_resource_logs","description":"Run a bounded, read-only query against one discovered Log Analytics workspace. Only approved tables, enumerated time windows, allowlisted filter fields, and up to 200 rows are supported. Never create or submit KQL.","parameters":{"type":"object","properties":{"workspace_id":{"type":"string","description":"Workspace ID returned by get_subscription_log_workspaces."},"table":{"type":"string","enum":["AzureActivity","AzureDiagnostics","ContainerLogV2","KubeEvents"]},"time_range":{"type":"string","enum":["5m","15m","1h","6h","24h","7d"]},"filter_field":{"type":["string","null"],"enum":["ActivityStatusValue","Category","CategoryValue","ContainerName","KubeEventType","Level","LogLevel","Name","Namespace","ObjectKind","OperationName","OperationNameValue","PodName","PodNamespace","Reason","Resource","ResourceId","ResultType","_ResourceId",null]},"filter_value":{"type":["string","null"]},"max_results":{"type":"integer","enum":[25,50,100,200]}},"required":["workspace_id","table","time_range","filter_field","filter_value","max_results"],"additionalProperties":false},"strict":true}
]'

request() {
  local method="$1" url="$2" body="${3:-}"
  local response status
  if [ -n "$body" ]; then
    response="$(curl -sS -X "$method" "$url" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data-binary "$body" -w $'\n%{http_code}')"
  else
    response="$(curl -sS -X "$method" "$url" -H "Authorization: Bearer $TOKEN" -w $'\n%{http_code}')"
  fi
  status="${response##*$'\n'}"
  response="${response%$'\n'*}"
  if [[ ! "$status" =~ ^2[0-9][0-9]$ ]]; then
    echo "Foundry API returned HTTP $status:" >&2
    printf '%s\n' "$response" >&2
    if [[ "$status" == "401" || "$status" == "403" ]]; then
      echo "Use an account with the Foundry User role on this project to read and create agent versions. Foundry Agent Consumer can invoke the agent but cannot manage it." >&2
    fi
    exit 1
  fi
  printf '%s' "$response"
}

VERSIONS="$(request GET "$PROJECT_ENDPOINT/agents/$AGENT_NAME/versions?api-version=$API_VERSION")"
VERSION="$(jq -r '.data | max_by(.version | tonumber) | .version // empty' <<< "$VERSIONS")"
[ -n "$VERSION" ] || { echo "No existing agent version found; refusing to replace or create an unverified agent." >&2; exit 1; }
CURRENT="$(request GET "$PROJECT_ENDPOINT/agents/$AGENT_NAME/versions/$VERSION?api-version=$API_VERSION")"
DEFINITION="$(jq -ce '.definition | .tools = ($tools | fromjson)' --arg tools "$TOOLS" <<< "$CURRENT")"
BODY="$(jq -cn --argjson definition "$DEFINITION" '{description:"AIOps assistant with backend-routed Azure Functions",definition:$definition}')"
CREATED="$(request POST "$PROJECT_ENDPOINT/agents/$AGENT_NAME/versions?api-version=$API_VERSION" "$BODY")"

jq '{name,version,model:.definition.model,tools:[.definition.tools[]?.name]}' <<< "$CREATED"
