# Azure AI Operations Assistant

## What is included

The standalone React chat client in `ops-assistant-ui/` signs users in with Microsoft Entra ID and sends access tokens only to the FastAPI backend. The backend accepts the assistant API only for the existing `Platform Administrator` and `Support Engineer` application roles.

The backend calls an existing Microsoft Foundry agent using the Entra-authenticated Azure AI Projects SDK. Its built-in, read-only tools:

- list non-sensitive Azure resource metadata;
- read reported Azure Resource Health; and
- query the last hour of Azure Monitor metrics for a metric advertised by the selected resource.

Inventory and monitoring are scoped to the development resource group, Terraform state resource group, and AKS managed node resource group. Terraform state storage data-plane access and secret values are not requested. Metric calls accept exact resource IDs only when they belong to one of those groups and verify the requested metric against Azure Monitor metric definitions.

The assistant does **not** currently query Log Analytics, application logs, Kubernetes pod events, or Prometheus, and it does not execute restarts or scale workloads. No shell, arbitrary KQL, or Azure write tool is exposed. The previously discussed restart confirmation and GitOps scale-PR workflows are not implemented yet; do not describe them as available.

The Terraform identity module creates a dedicated AKS workload identity with `Reader` and `Monitoring Reader` at the three resource-group scopes. Reader permissions on `eitoap-tfstate-rg` permit Azure Resource Manager metadata reads only; no blob/data-plane role is assigned. Grant this identity only the specific Foundry project role needed to invoke the pre-created agent. Do not grant Contributor, Owner, Storage Blob Data Reader, or broad subscription roles.

## Required Azure prerequisites

The Azure CLI must be signed into the subscription that owns the named EITOAP resource groups. The previous local login could see only a different subscription, so Terraform planning/applying and Azure deployment are blocked until the correct subscription and tenant access are available. A different AWS account/project does not supply Azure permissions.

Before creating resources:

1. Confirm the subscription ID and tenant with an administrator, and sign in using an Azure identity that can read the existing resource groups and create the assistant identity, role assignments, and Static Web App.
2. Rotate any credentials that were committed in development Helm values or exposed in logs/screenshots. Do not reuse them for the assistant.
3. Check Foundry Agents Service availability, model deployment availability/quota, Static Web Apps availability, region, network egress from AKS, and cost in the selected subscription.
4. Review the Terraform plan, especially the new identity role assignments to the three existing resource groups. Applying Terraform changes permissions and must be approved by the subscription owner.
5. Create a Microsoft Foundry project and model deployment; create an agent named for the deployment configuration and grant the new managed identity the minimum Foundry project role needed to invoke it.
6. Configure the existing backend Entra API registration with an exposed delegated scope (for example `access_as_user`) and grant the assistant UI Entra app access to that API. The backend must validate the API audience, tenant, and operator app roles.

## Provision and configure

From `infrastructure/terraform/environments/dev/`, after confirming the Azure CLI subscription:

```powershell
az account show --query "{subscription:id,tenant:tenantId,name:name}" -o json
terraform init
terraform plan
```

Do not run `terraform apply` until the reviewed plan targets the correct subscription and the state backend can be safely accessed. The module `ops_assistant_identity_client_id` output is used by the backend chart; it is not an API key.

Configure the following non-secret values after the Foundry project, agent, and Static Web App exist:

- `FOUNDRY_PROJECT_ENDPOINT`: the project endpoint shown in Foundry.
- `FOUNDRY_AGENT_NAME`: the existing agent name.
- `OPS_AZURE_SUBSCRIPTION_ID`: the subscription containing the three resource groups.
- `OPS_ASSISTANT_ALLOWED_ORIGINS`: the exact HTTPS origin of the Static Web App (no wildcard).
- `backend.opsAssistant.clientId`: Terraform output `ops_assistant_identity_client_id`.
- `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_TENANT_ID`, `VITE_ASSISTANT_API_SCOPE`, and `VITE_ASSISTANT_API_URL` for the static UI build.

The backend chart's workload identity is disabled by default. Enable `backend.opsAssistant.enabled` only after setting its identity client ID. This adds the annotated `ops-assistant` service account and workload-identity pod label. It does not grant Kubernetes API permissions.

After the UI exists and its origin is configured, add the origin to the backend CORS allowlist and redeploy. The UI's API endpoint must be reachable over HTTPS from the browser.

## Deploy the separate UI

Set repository variable `VITE_ENTRA_CLIENT_ID`, `VITE_ENTRA_TENANT_ID`, `VITE_ASSISTANT_API_SCOPE`, and `VITE_ASSISTANT_API_URL` for the `ops-assistant-ui` Vite build. Add the Static Web Apps deployment token as the GitHub Actions secret `AZURE_STATIC_WEB_APPS_API_TOKEN`. The workflow `.github/workflows/ops-assistant-ui.yml` deploys the separate UI on changes to `ops-assistant-ui/` on `master` or by manual dispatch.

For local UI development, install dependencies in `ops-assistant-ui/`, copy `.env.example` to `.env.local`, configure the Entra app and API scope, and run `npm run dev`. The Vite development server proxies `/api` to `http://localhost:8000`.

## Validation and operational limits

- Backend tests cover message bounds, resource-group scoping, metric allowlisting, and rejection of unregistered tools.
- Build and run the backend and Static Web App CI workflows before deployment.
- If the Foundry endpoint/agent or Azure subscription is unconfigured, the API returns an explicit service-unavailable error. Azure upstream failures return a bounded gateway error; no healthy/default response is fabricated.
- Resource-health results may be absent for some Azure resources. Missing records are reported as unavailable, not healthy.
- Azure Monitor may not publish every metric for every resource type. The tool validates availability before requesting a one-hour, 15-minute aggregate.
- Chat context is client-supplied and bounded; do not treat it as an audit record. The assistant instructions treat retrieved text as untrusted and prohibit secret/state disclosure.
- The first version is advisory and read-only. Add Log Analytics, live AKS diagnostics, confirmation-gated restarts, and GitOps scale PRs as separately reviewed changes with dedicated least-privilege identities and audit trails.
