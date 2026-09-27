# Phase 4: Observability

## Inspection findings and implementation plan

- The backend is FastAPI, with a shared API, an API gateway, and individual service entry points. Kubernetes deploys the backend through Helm; local development uses Docker Compose.
- `/health`, `/live`, `/ready`, and Kubernetes probe aliases already existed. The root `/metrics` endpoint only returned static info/health gauges, and `/api/v1/metrics` was an empty stub. The root path is now canonical; the existing API path remains a backward-compatible alias to the same Prometheus registry.
- Logs already went to stdout with timestamps and request IDs, but structured output included user IDs and debug SMS logs contained message contents. Some errors also logged provider/connection details.
- Kubernetes startup, liveness, and readiness probes, backend resource requests/limits, the `monitoring` namespace, and a backend NetworkPolicy already existed. Prometheus, Grafana, exporters, provisioned dashboards, and alert rules did not.
- The development Terraform environment already provisions Azure Application Insights with Log Analytics. This implementation reuses the Kubernetes/Helm architecture and adds no Azure services.
- CI runs backend tests, Ruff, Black, isort, Bandit, and application-import validation. Dependencies are pinned, and CI installs a hash-locked requirements file.

The implementation keeps those existing patterns: FastAPI Prometheus instrumentation, bounded business counters, stdout request-correlated logs with privacy redaction, and a separate Helm chart. Prometheus scrapes annotated backend pods plus Kubernetes state and cAdvisor metrics. Grafana dashboards, a Prometheus datasource, and alert rules are provisioned from version-controlled files. No tracing backend or unnecessary Azure services are introduced.

## Architecture

```text
Application
    ↓
Prometheus metrics (/metrics)
    ↓
Prometheus
    ↓
Grafana
    ↓
Dashboards / Alerts
```

The backend Helm chart annotates its pods for scrape discovery. Prometheus uses Kubernetes service-account RBAC to discover those pods, Kubernetes object state, and kubelet cAdvisor endpoints. Grafana is configured with Prometheus as its datasource and loads both dashboards from the observability chart.

## Application metrics

The shared instrumentation in `backend/app/core/metrics.py` is applied to the monolith, gateway, and each FastAPI service entry point. `prometheus-fastapi-instrumentator` exposes `/metrics` and records `http_requests_total` (HTTP method, route template, and exact response status) plus request-duration histograms. The existing `/api/v1/metrics` route renders the same registry for compatibility. Unmatched routes and metrics scrapes from both paths are excluded to avoid high-cardinality labels and self-generated traffic.

Additional counters:

| Metric | Labels | Meaning |
|---|---|---|
| `eitoap_password_reset_events_total` | `stage=request|completion`, `outcome=attempt|success|failure` | Reset initiation and reset completion outcomes |
| `eitoap_otp_verifications_total` | `outcome=attempt|success|failure` | OTP verification outcomes |
| `eitoap_authentication_failures_total` | `status_code=401|403` | Authentication and authorization failures |

Metrics never include email addresses, user IDs, phone numbers, passwords, OTPs, tokens, request IDs, or raw URLs. The HTTP instrumentation uses route templates rather than concrete request paths.

## Logging and privacy

Container deployments set `LOG_FORMAT=json`; logs remain on stdout for Kubernetes collection. JSON entries include an ISO-8601 UTC timestamp, severity, module, safe operation name, and a UUID request ID. The gateway forwards that ID to downstream services. Local development retains the readable text formatter unless `LOG_FORMAT=json` is set.

Operational logs omit user IDs, email addresses, IP addresses, phone numbers, request bodies, SMS contents, and arbitrary `extra` fields. Uvicorn access logging is disabled because its default records include client addresses and raw request paths; HTTP counts, status, and latency remain available through metrics. Exception output records only the exception type, not exception messages or tracebacks that could contain credentials or personal data. Incoming request IDs are accepted only as UUIDs; other values are replaced with generated UUIDs. Existing audit records are a separate application data store and are not used as metric labels.

## Kubernetes monitoring and dashboards

Install `deploy/helm/observability` in the existing `monitoring` namespace. It deploys:

- Prometheus with 30-day retention and an 8 GiB persistent volume claim.
- `kube-state-metrics` for pod readiness/restarts and desired/available deployment replicas.
- Prometheus cAdvisor scraping of kubelet `/metrics/cadvisor` endpoints for pod/container CPU and memory.
- Grafana with persistent storage, a preconfigured Prometheus datasource, and file-provisioned dashboards.

The backend NetworkPolicy permits port 8000 from only the Prometheus pod in the monitoring namespace, in addition to its existing traffic rules. Grafana and Prometheus are `ClusterIP` services; no public ingress or default credentials are configured. Create the `grafana-admin` Kubernetes Secret out of band before installing the chart.

The **EITOAP Application** dashboard includes request rate, 4xx/5xx ratio, p95 latency, 5xx rate, password-reset request/completion outcomes, OTP outcomes, and authentication failures. The **EITOAP Kubernetes** dashboard includes backend pod CPU, memory, restarts, and desired-versus-available replicas.

## Alerts and operator response

Prometheus evaluates the rules in the observability chart. An operator can inspect current state at the Prometheus `/alerts` page.

| Alert | Trigger | Initial investigation |
|---|---|---|
| `HighHttp5xxRate` | 5xx exceed 5% of requests at more than 0.2 requests/second for 5 minutes | Check backend logs, recent releases, and PostgreSQL/Redis/provider health |
| `HighHttpRequestLatency` | p95 request latency exceeds 1 second for 10 minutes | Check slow routes, database/Redis latency, and CPU/memory saturation |
| `BackendUnavailable` | No scrape target or a failed backend scrape for 2 minutes | Check readiness, service discovery, backend pod events, and NetworkPolicy |
| `BackendPodUnavailable` | A backend pod is unready for 5 minutes | Check probe failures, scheduling, dependencies, and pod events |
| `BackendPodRestarting` | At least 3 restarts in 15 minutes | Check `kubectl logs --previous`, events, and OOM/resource limits |
| `BackendReplicasUnavailable` | Available deployment replicas remain below desired for 5 minutes | Check rollout status, scheduling, image pulls, probes, and cluster capacity |

Rules are deliberately sustained and volume-gated where appropriate to reduce noise. They evaluate and appear in Prometheus, but no Alertmanager receiver or external notification channel is configured; notifications require an operator-owned destination and credentials.

## Basic SLIs and SLOs

These are learning targets for a low-volume project, not an availability guarantee. Evaluate over a rolling 28-day window; Prometheus retains 30 days so the whole window is available.

| Indicator | Prometheus measurement | Initial SLO |
|---|---|---|
| Request availability | `2xx`/`3xx` requests divided by all observed backend requests | At least 99.5% |
| HTTP server error rate | `5xx` requests divided by all observed backend requests | At most 1% |
| Latency | Requests completed within 500 ms divided by observed backend requests, from the duration histogram | At least 95% |

Example PromQL for the 28-day availability ratio:

```promql
sum(increase(http_requests_total{job="eitoap-backend",status=~"2..|3.."}[28d]))
/
sum(increase(http_requests_total{job="eitoap-backend"}[28d]))
```

The 5xx ratio substitutes `status=~"5.."` in the numerator. The latency ratio uses `http_request_duration_seconds_bucket{le="0.5"}` in the numerator and `http_request_duration_seconds_count` in the denominator. Dashboards show shorter operational windows; these queries let an operator assess the SLO window directly.

These request-based SLIs need traffic to produce a value. `up{job="eitoap-backend"}` independently shows whether the metrics endpoint is scrapeable, but is not a substitute for measuring real user requests. No dedicated SLO platform or synthetic-probe service is included.

## Deploy and verify

1. Update the existing backend Helm release so its pods have the scrape annotation and its NetworkPolicy allows Prometheus. Keep the deployment's existing values and secret provider:

   ```sh
   helm upgrade <existing-backend-release> deploy/helm/backend \
     --namespace backend --reuse-values --wait
   ```

   The Kustomize base backend manifest also includes the scrape annotation.

2. Create the Grafana admin Secret in the `monitoring` namespace using a secret manager or a secure local file that is not in the repository. The chart expects secret name `grafana-admin`, key `admin-password`.

3. Install or update the observability chart:

   ```sh
   helm upgrade --install observability deploy/helm/observability \
     --namespace monitoring --create-namespace --wait
   ```

4. Verify pods and services:

   ```sh
   kubectl get pods -n backend
   kubectl get pods -n monitoring
   kubectl get svc -n monitoring
   kubectl logs deployment/prometheus -n monitoring
   kubectl logs deployment/grafana -n monitoring
   ```

5. Port-forward the backend and check the exposition:

   ```sh
   kubectl port-forward -n backend svc/backend-service 8000:8000
   curl.exe http://localhost:8000/metrics
   ```

   Expect `http_requests_total`, `http_request_duration_seconds_bucket`, and the `eitoap_*` counters after exercising the corresponding flows.

6. In separate terminals, access Prometheus and Grafana:

   ```sh
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   kubectl port-forward -n monitoring svc/grafana 3000:80
   ```

   Open Prometheus at `http://localhost:9090` and Grafana at `http://localhost:3000`. Grafana dashboards are provisioned automatically; sign in with the admin password stored in the Kubernetes Secret.

7. In Prometheus, inspect **Status → Targets** for `eitoap-backend`, `kube-state-metrics`, and `kubernetes-cadvisor`, then inspect **Alerts** for rule evaluation. Exercise an application endpoint and check that its request counter and histogram change.

### Troubleshooting

- **Backend target missing/down:** Check pod annotation and readiness with `kubectl get pods -n backend --show-labels`; inspect the backend NetworkPolicy and `kubectl describe pod`.
- **Kubernetes resource panels empty:** Check the Prometheus `kube-state-metrics` and `kubernetes-cadvisor` targets and its ClusterRole; kubelet access is cluster-specific.
- **Grafana cannot load dashboards/data:** Check `kubectl logs deployment/grafana -n monitoring`, then verify its datasource URL and Prometheus target health.
- **Grafana pod not starting:** Confirm the `grafana-admin` Secret exists with the expected key and that both PVCs are bound using `kubectl get pvc -n monitoring`.
- **Metrics endpoint fails:** Inspect `kubectl logs deployment/backend-deployment -n backend` and port-forward to the backend service before debugging Prometheus.

## Scope and limitations

- No OpenTelemetry tracing SDK/exporter is added: the current request flow has no trace collector/backend, and UUID request correlation provides useful log linkage without introducing a second telemetry pipeline.
- The Azure Application Insights/Log Analytics Terraform configuration remains unchanged.
- Prometheus, Grafana, and kube-state-metrics each run as a single replica. This is suitable for a learning/portfolio cluster, not a highly available monitoring control plane.
- Kubelet cAdvisor scraping uses the in-cluster service-account token and skips kubelet serving-certificate verification because cluster node certificates are not consistently addressable by node IP. Keep this scrape internal and review cluster-specific certificate support before production hardening.
- The default Prometheus/Grafana PVC sizes and retention are starting points; review disk use and adjust values as cluster/cardinality grow.
- Alert rules evaluate in Prometheus but do not notify until an Alertmanager receiver or another notification integration is configured.

## Interview concepts

- **Metrics vs logs vs traces:** metrics aggregate numeric behavior over time, logs explain individual events, and traces show one request across multiple services. This phase instruments metrics and safe correlated logs; it does not add a trace backend.
- **Prometheus pull model and `/metrics`:** Prometheus periodically scrapes the application's text exposition endpoint. The application does not need credentials for a metrics push service.
- **Exporters:** `kube-state-metrics` translates Kubernetes API object state into Prometheus series; kubelet cAdvisor provides container resource usage. They complement application instrumentation rather than replacing it.
- **Grafana vs Prometheus:** Prometheus scrapes, stores, and evaluates PromQL/alert rules; Grafana queries Prometheus and presents provisioned dashboards.
- **RED metrics:** request rate, error rate, and duration (latency) are the primary request-oriented signals on the application dashboard.
- **SLIs vs SLOs:** an SLI is the measured service behavior; an SLO is the target for that indicator over a defined window. The targets here are explicit and can be evaluated with PromQL.
- **Kubernetes observability:** application HTTP/business counters show service behavior, kube-state-metrics shows workload state, and cAdvisor shows container resource usage. Probe and deployment metrics help separate application failures from scheduling or resource issues.
- **Alerting:** useful alerts have a meaningful condition, a sustained duration, a severity, and a first investigation step. Notifications need an owned receiver; rules alone do not page anyone.
- **Why it matters in production:** observability shortens detection and diagnosis time, reveals regressions and resource constraints, and lets operators reason about user experience rather than relying on “pod is running.”
- **SRE workflow:** define SLIs/SLOs, instrument services, observe dashboards, alert on actionable symptoms, investigate with correlated logs and workload metrics, mitigate, and use what was learned to improve reliability.
