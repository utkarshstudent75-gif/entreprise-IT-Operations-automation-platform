# Azure AI Operations Assistant

## What is included

The standalone React chat client in `ops-assistant-ui/` signs users in with Microsoft Entra ID and sends access tokens only to the FastAPI backend. The backend accepts the assistant API only for the existing `Platform Administrator` and `Support Engineer` application roles.

The backend calls the configured Microsoft Foundry agent using the Entra-authenticated Azure AI Projects SDK. The Foundry tool loop dispatches to separate, HTTP-triggered Azure Functions for read-only tools:

- list non-sensitive Azure resource metadata across the configured subscription;
- read reported Azure Resource Health across that subscription;
- query the last hour of an Azure Monitor metric advertised by a resource in that subscription; and
- discover every Log Analytics workspace in the configured subscription and query approved tables in those workspaces.

This follows the linked AWS demo's interaction model: the agent invokes focused functions for logs, metrics, and health while investigating a user request. The Azure Functions are on-demand tool endpoints, not timer jobs. The agent correlates returned health, metrics, and log evidence, explains the most likely root cause, distinguishes evidence from hypotheses, and suggests a safe next step. It remains read-only; recommendations require a human to act.

The Log Analytics tool supports `AzureActivity`, `AzureDiagnostics`, `ContainerLogV2`, and `KubeEvents`, with fixed time windows (5 minutes, 15 minutes, 1 hour, 6 hours, 24 hours, or 7 days), table-specific filter fields, and a maximum of 200 rows. KQL is assembled by the backend from these allowlisted values; users and the model cannot submit arbitrary KQL. Queries are additionally filtered to resource scope in the configured subscription. Returned rows and response size are bounded, with best-effort redaction of common credential patterns. Redaction is not a guarantee that logs contain no sensitive data. Workspace discovery does not enable diagnostic ingestion: logs are available only when resource diagnostic settings send them to a discovered workspace; for example, AKS container logs require the relevant Container Insights/diagnostic collection.

Alerts are separate from on-demand agent tools. Azure Monitor alert rules and Action Groups invoke the `alerts/monitor` HTTP-triggered Function using the common alert schema. The Function normalizes the event and sends it to an authenticated backend endpoint; Redis maintains active findings (expiring after seven days if Azure does not send a resolution) and publishes changes to an authenticated Server-Sent Events stream. The signed-in UI holds that stream only while its tab is visible; it does not poll Azure every minute or send email/Teams/browser-closed notifications. Configure Azure Monitor rules for Resource Health, failed Activity Log operations, and the approved log signals; a workspace with no diagnostic ingestion cannot produce log alerts.

The assistant does not query the Kubernetes API, Prometheus, or arbitrary application data sources, and it does not execute restarts or scale workloads. No shell, arbitrary KQL, or Azure write tool is exposed. The linked AWS demo's Prometheus-specific metrics and direct EKS health checks require Azure-side equivalents (for example, Azure Monitor metrics and Container Insights/AKS diagnostics); those data sources are not available unless configured. The previously discussed restart confirmation and GitOps scale-PR workflows are not implemented; do not describe them as available.

The Terraform identity module creates a dedicated user-assigned identity with `Reader`, `Monitoring Reader`, and `Log Analytics Reader` at the selected subscription scope. This allows discovery and log access across every Log Analytics workspace in that subscription, including workspaces unrelated to the project; review and approve this broad read scope with the subscription owner. Attach the same identity to the Function App so its Azure SDK calls use that least-privilege identity. No Storage Blob data-plane role is assigned, so Terraform state contents remain inaccessible. The identity is provisioned from the isolated `infrastructure/terraform/environments/ops-assistant-dev/` root and uses the separate `ops-assistant-dev.terraform.tfstate` backend key. That root manages only the assistant identity, its federated credential, and its read-only role assignments; the AKS OIDC issuer URL is supplied as an input, so this root does not read or manage AKS configuration or reconcile the existing application infrastructure. Grant this identity only the specific Foundry project role needed to invoke the pre-created agent. Do not grant Contributor, Owner, or Storage Blob Data Reader.

## Required Azure prerequisites

The Azure CLI must be signed into the selected Azure subscription that owns the EITOAP deployment. The previous local login could see only a different subscription, so Terraform planning/applying and Azure deployment are blocked until the correct subscription and tenant access are available. A different AWS account/project does not supply Azure permissions.

Before creating resources:

1. Confirm the subscription ID and tenant with an administrator, and sign in using an Azure identity that can read the existing resource groups and create the assistant identity, role assignments, Function App, and Static Web App.
   Ensure `ops-api.itproject.in` has an A record to the AKS ingress public IP (`52.226.152.209`) before issuing a TLS certificate. The dev frontend ingress values configure this hostname and redirect HTTP to HTTPS.
2. Rotate any credentials that were committed in development Helm values or exposed in logs/screenshots. Do not reuse them for the assistant.
3. Check Foundry Agents Service availability, model deployment availability/quota, Azure Functions and Storage availability, Static Web Apps availability, region, network egress from AKS and Functions, and cost in the selected subscription.
4. Review the Terraform plan, especially the subscription-wide `Reader`, `Monitoring Reader`, and `Log Analytics Reader` assignments. The last role grants log-reading access to every workspace in the subscription. Applying Terraform changes permissions and must be approved by the subscription owner.
5. Create a Microsoft Foundry project and model deployment; create an agent named for the deployment configuration and grant the new managed identity the minimum Foundry project role needed to invoke it.
6. Configure the existing backend Entra API registration with an exposed delegated scope (for example `access_as_user`) and grant the assistant UI Entra app access to that API. The backend must validate the API audience, tenant, and operator app roles.

## Provision and configure

From `infrastructure/terraform/environments/ops-assistant-dev/`, after confirming the Azure CLI subscription:

```powershell
az account show --query "{subscription:id,tenant:tenantId,name:name}" -o json
terraform init
terraform plan
```

The separate state key ensures an assistant plan contains only the assistant identity, federated credential, and three subscription-scoped read roles. The AKS OIDC issuer is supplied in `terraform.tfvars`; no workspace list is required because the Functions discover workspaces through Azure Resource Graph. Confirm the plan contains only the expected identity, federated credential, and role assignments, with no changes or deletions to the application infrastructure, before applying. This does not resolve drift in the full dev Terraform root; continue to review that root separately and do not apply its plan until unrelated changes are understood. The `ops_assistant_identity_client_id` output is used by both the backend and Function App; it is not an API key.

Configure the following non-secret values after the Foundry project, agent, and Static Web App exist:

- `FOUNDRY_PROJECT_ENDPOINT`: the project endpoint shown in Foundry.
- `FOUNDRY_AGENT_NAME`: the existing agent name.
- `OPS_AZURE_SUBSCRIPTION_ID`: the subscription the assistant may inspect.
- `OPS_ASSISTANT_FUNCTIONS_BASE_URL`: the Function App's HTTPS `/api` base URL in the backend configuration.
- `OPS_ASSISTANT_ALLOWED_ORIGINS`: the exact HTTPS origin of the Static Web App (no wildcard).
- Store the generated Function key as Key Vault secret `ops-assistant-functions-key`; the backend loads it at startup and sends it only in the `x-functions-key` header.
- Store a random shared alert-ingest token as Key Vault secret `ops-assistant-alert-ingest-token`. Configure the same value in the Function App through a Key Vault reference, and set `OPS_ASSISTANT_ALERT_INGEST_URL` there to the backend `/api/v1/ops-assistant/alerts/events` HTTPS endpoint.
- `backend.opsAssistant.clientId`: Terraform output `ops_assistant_identity_client_id`, stored in `deploy/helm/values/ops-assistant-dev.yaml`.
- `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_TENANT_ID`, `VITE_ASSISTANT_API_SCOPE`, and `VITE_ASSISTANT_API_URL` for the static UI build.

The assistant dev override sets `backend.opsAssistant.enabled` and the Terraform output `ops_assistant_identity_client_id`; the backend Argo CD application loads this override after the existing dev values. This adds the annotated `ops-assistant` service account and workload-identity pod label. It does not grant Kubernetes API permissions.

After the UI exists and its origin is configured, add the origin to the backend CORS allowlist and redeploy. The UI's API endpoint must be reachable over HTTPS from the browser.

### Enable TLS for the AKS ingress

The dev ingress uses cert-manager with the `letsencrypt-prod` ClusterIssuer and HTTP-01 validation through NGINX. Install cert-manager in the AKS cluster, create the ClusterIssuer using a valid operator email, and sync the frontend Argo CD application. Confirm the `eitoap-api-tls` secret is issued in the `frontend` namespace and verify `https://ops-api.itproject.in/api/health` before configuring it as the Functions alert-ingest origin.

## Deploy Azure Functions

Deploy the Python Functions project from `backend/` to a Python 3.12 Azure Function App (Functions runtime v4) with a Storage account. From that directory, use Azure Functions Core Tools: `func azure functionapp publish <function-app-name> --python`. The Functions package uses the smaller `requirements-functions.txt` dependency set rather than installing the full backend requirements. The app exposes function-key-protected endpoints for inventory, resource health, metrics, workspace discovery, curated logs, and Azure Monitor alert delivery.

Attach the Terraform user-assigned identity to the Function App and configure its client ID as `AZURE_CLIENT_ID`; set `OPS_AZURE_SUBSCRIPTION_ID` and `KEYVAULT_NAME` in the Function App configuration. Grant that identity Key Vault Secrets User access to the assistant vault. Configure `OPS_ASSISTANT_ALERT_INGEST_URL` and resolve `OPS_ASSISTANT_ALERT_INGEST_TOKEN` via a Key Vault reference. Retrieve a Function key after publishing, store it in Key Vault as `ops-assistant-functions-key`, set the Function App `/api` URL in `config.opsAssistantFunctionsBaseUrl`, then deploy the backend.

Create Azure Monitor Action Groups with the `alerts/monitor` Function receiver and common alert schema enabled. Add subscription-scope Resource Health and Activity Log alert rules, plus scheduled-query alert rules for the required log conditions in each workspace. Configure resource diagnostic settings/Container Insights to send the desired logs to Log Analytics; workspace discovery alone does not create alert rules or enable ingestion. The Function key secures inbound Azure Monitor/agent calls; the separate Key Vault token authenticates Function-to-backend alert events.

## Deploy the separate UI

Set repository variable `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_TENANT_ID`, `VITE_ASSISTANT_API_SCOPE`, and `VITE_ASSISTANT_API_URL` for the `ops-assistant-ui` Vite build. Add the Static Web Apps deployment token as the GitHub Actions secret `AZURE_STATIC_WEB_APPS_API_TOKEN`. The workflow `.github/workflows/ops-assistant-ui.yml` deploys the separate UI on changes to `ops-assistant-ui/` on `master` or by manual dispatch.

For local UI development, install dependencies in `ops-assistant-ui/`, copy `.env.example` to `.env.local`, configure the Entra app and API scope, and run `npm run dev`. The Vite development server proxies `/api` to `http://localhost:8000`.

## Validation and operational limits

- Backend tests cover conversation bounds, Azure Functions tool dispatch, subscription scoping, metric allowlisting, workspace discovery and enforcement, curated Log Analytics query limits, alert-event authentication/normalization, and rejection of unregistered tools.
- Build and run the backend and Static Web App CI workflows before deployment.
- If the Foundry endpoint/agent or Azure subscription is unconfigured, the API returns an explicit service-unavailable error. Azure upstream failures return a bounded gateway error; no healthy/default response is fabricated.
- Resource-health results may be absent for some Azure resources. Missing records are reported as unavailable, not healthy.
- Azure Monitor may not publish every metric for every resource type. The tool validates availability before requesting a one-hour, 15-minute aggregate.
- Chat context is client-supplied and bounded; do not treat it as an audit record. Log data can contain sensitive or attacker-controlled text; restrict workspace access, configure ingestion carefully, and review retention and data-handling requirements. The assistant instructions treat retrieved text as untrusted and prohibit secret/state disclosure.
- The assistant is advisory and read-only. Add live Kubernetes API diagnostics, Prometheus, confirmation-gated restarts, and GitOps scale PRs only as separately reviewed changes with dedicated least-privilege identities and audit trails.
