import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.ops_assistant import (
    OpsAssistantAlert,
    OpsAssistantAlertsResponse,
    OpsAssistantMessage,
    OpsResource,
    OpsResourceHealth,
)

logger = logging.getLogger("itpa")

MAX_RESOURCE_RESULTS = 1000
MAX_RESOURCE_PAGES = 20
MAX_TOOL_ROUNDS = 1
MAX_LOG_RESULTS = 200
MAX_LOG_RESPONSE_CHARACTERS = 24000
LOG_TIME_RANGES = {
    "5m": {"kql": "5m", "timespan": "PT5M"},
    "15m": {"kql": "15m", "timespan": "PT15M"},
    "1h": {"kql": "1h", "timespan": "PT1H"},
    "6h": {"kql": "6h", "timespan": "PT6H"},
    "24h": {"kql": "24h", "timespan": "P1D"},
    "7d": {"kql": "7d", "timespan": "P7D"},
}
LOG_TABLES: dict[str, dict[str, Any]] = {
    "AzureActivity": {
        "columns": (
            "TimeGenerated",
            "SubscriptionId",
            "OperationNameValue",
            "ActivityStatusValue",
            "ActivitySubstatusValue",
            "ResourceId",
            "CategoryValue",
        ),
        "scope_field": "SubscriptionId",
        "scope_type": "subscription_id",
        "filter_fields": (
            "OperationNameValue",
            "ActivityStatusValue",
            "ResourceId",
            "CategoryValue",
        ),
    },
    "AzureDiagnostics": {
        "columns": (
            "TimeGenerated",
            "SubscriptionId",
            "Category",
            "OperationName",
            "ResultType",
            "Resource",
            "ResourceId",
            "Level",
        ),
        "scope_field": "SubscriptionId",
        "scope_type": "subscription_id",
        "filter_fields": (
            "Category",
            "OperationName",
            "ResultType",
            "Resource",
            "ResourceId",
            "Level",
        ),
    },
    "ContainerLogV2": {
        "columns": (
            "TimeGenerated",
            "_ResourceId",
            "PodNamespace",
            "PodName",
            "ContainerName",
            "LogLevel",
            "LogMessage",
        ),
        "scope_field": "_ResourceId",
        "scope_type": "resource_id",
        "filter_fields": ("PodNamespace", "PodName", "ContainerName", "LogLevel"),
    },
    "KubeEvents": {
        "columns": (
            "TimeGenerated",
            "_ResourceId",
            "Namespace",
            "Name",
            "ObjectKind",
            "KubeEventType",
            "Reason",
            "Message",
            "SourceComponent",
        ),
        "scope_field": "_ResourceId",
        "scope_type": "resource_id",
        "filter_fields": (
            "Namespace",
            "Name",
            "ObjectKind",
            "KubeEventType",
            "Reason",
        ),
    },
}
LOG_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key|client[_-]?secret|"
        r"access[_-]?key|connection[_-]?string)([\"']?\s*[:=]\s*[\"']?)([^\"'\s,;]+)"
    ),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)

AGENT_POLICY = """You are the read-only Azure operations assistant for the EITOAP project.
You are a helpful, knowledgeable AI assistant that speaks naturally and conversationally.

CORE PRINCIPLES:
- Be conversational, helpful, and natural - like a knowledgeable colleague
- Be concise but complete - give complete answers without unnecessary verbosity
- Use natural language, not log format or structured reports
- Summarize tool results in your own words - never dump raw tool output
- For simple questions: give a direct, natural answer in 2-4 sentences
- For incidents: give a clear narrative - what happened, why, what to do next
- Use bullet points sparingly, only for lists or action items
- Say "I don't know" or "data unavailable" instead of guessing

TOOL USAGE:
- Use tools when you need current data (inventory, health, metrics, logs)
- After getting tool results, synthesize them into a natural response
- Never dump raw tool output - always summarize in your own words
- If a tool fails, acknowledge it naturally and work with what you have

RESPONSE STYLE:
- Write like you're talking to a colleague, not writing a report
- Use "I found..." "It looks like..." "The issue appears to be..." 
- Avoid: "Observed facts:", "Supporting evidence:", "Hypothesis:", "Confidence:"
- Instead: "I found that..." "This suggests..." "The likely cause is..."

FOR INCIDENTS:
- Start with what you found (the likely cause)
- Explain the evidence briefly
- Give 1-3 clear next steps
- Keep it under 5-6 sentences total unless more detail is needed

BOUNDARIES:
- Read-only: never claim to change infrastructure
- No credentials, secrets, or personal data
- When data is missing, say so honestly
- Distinguish facts from hypotheses clearly"""

RESOURCE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_azure_resource_inventory",
        "description": (
            "List non-sensitive Azure resource metadata across the configured subscription. "
            "Does not read Terraform state contents or secret values."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_azure_resource_health",
        "description": (
            "Get reported Azure Resource Health states for resources in the configured "
            "subscription. Missing health results are not proof "
            "that resources are healthy."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_azure_resource_metrics",
        "description": (
            "Read the most recent hour of an available Azure Monitor metric for one "
            "exact resource ID returned by the resource inventory tool. Use the "
            "resource's supported metric name; this tool cannot query logs or change "
            "resources."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "resource_id": {
                    "type": "string",
                    "description": "Exact Azure resource ID from the configured inventory.",
                },
                "metric_name": {
                    "type": "string",
                    "description": "Exact Azure Monitor metric name supported by the resource.",
                },
            },
            "required": ["resource_id", "metric_name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_subscription_log_workspaces",
        "description": (
            "Discover Log Analytics workspace IDs in the configured Azure subscription. "
            "The assistant can query approved log tables in any workspace returned here."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "query_azure_resource_logs",
        "description": (
            "Run a bounded, read-only query against one Log Analytics workspace returned "
            "by get_subscription_log_workspaces. "
            "Only approved tables, enumerated time windows, table-specific allowlisted filter "
            "fields, and up to 200 rows are supported. Never create or submit KQL."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {
                    "type": "string",
                    "description": "Workspace ID returned by get_subscription_log_workspaces.",
                },
                "table": {"type": "string", "enum": list(LOG_TABLES)},
                "time_range": {"type": "string", "enum": list(LOG_TIME_RANGES)},
                "filter_field": {
                    "type": ["string", "null"],
                    "enum": sorted(
                        {
                            field
                            for table_config in LOG_TABLES.values()
                            for field in table_config["filter_fields"]
                        }
                    )
                    + [None],
                },
                "filter_value": {"type": ["string", "null"]},
                "max_results": {
                    "type": "integer",
                    "enum": [25, 50, 100, MAX_LOG_RESULTS],
                },
            },
            "required": [
                "workspace_id",
                "table",
                "time_range",
                "filter_field",
                "filter_value",
                "max_results",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

FUNCTION_TOOL_ROUTES = {
    "get_azure_resource_inventory": "tools/inventory",
    "get_azure_resource_health": "tools/health",
    "get_azure_resource_metrics": "tools/metrics",
    "get_subscription_log_workspaces": "tools/log-workspaces",
    "query_azure_resource_logs": "tools/logs",
}


class OpsAssistantNotConfigured(Exception):
    pass


class OpsAssistantUpstreamError(Exception):
    pass


def _configured_subscription_id() -> str:
    subscription_id = settings.OPS_AZURE_SUBSCRIPTION_ID
    if not subscription_id:
        raise OpsAssistantNotConfigured("Azure resource monitoring is not configured.")
    try:
        return str(UUID(subscription_id))
    except ValueError as exc:
        raise OpsAssistantNotConfigured(
            "The configured Azure subscription ID is invalid."
        ) from exc


def _resource_graph_query(query: str) -> list[dict[str, Any]]:
    subscription_id = _configured_subscription_id()

    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    try:
        access_token = credential.get_token(
            "https://management.azure.com/.default"
        ).token
        rows: list[dict[str, Any]] = []
        skip_token = None
        seen_skip_tokens = set()
        pages_read = 0
        while True:
            if pages_read >= MAX_RESOURCE_PAGES:
                raise OpsAssistantUpstreamError(
                    "Azure Resource Graph returned too many resource pages."
                )
            pages_read += 1
            options: dict[str, Any] = {"$top": MAX_RESOURCE_RESULTS}
            if skip_token:
                if skip_token in seen_skip_tokens:
                    raise OpsAssistantUpstreamError(
                        "Azure Resource Graph returned a repeated page token."
                    )
                seen_skip_tokens.add(skip_token)
                options["$skipToken"] = skip_token
            response = httpx.post(
                "https://management.azure.com/providers/Microsoft.ResourceGraph/"
                "resources?api-version=2022-10-01",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "subscriptions": [subscription_id],
                    "query": query,
                    "options": options,
                },
                timeout=20.0,
            )
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise OpsAssistantUpstreamError(
                    "Azure Resource Graph returned an invalid response."
                ) from exc
            if not isinstance(payload, dict):
                raise OpsAssistantUpstreamError(
                    "Azure Resource Graph returned an invalid response."
                )
            page = payload.get("data")
            if not isinstance(page, list):
                raise OpsAssistantUpstreamError(
                    "Azure Resource Graph returned an invalid response."
                )
            rows.extend(row for row in page if isinstance(row, dict))
            skip_token = payload.get("$skipToken")
            if not isinstance(skip_token, str) or not skip_token or not page:
                break
        return rows
    except AzureError as exc:
        logger.error(
            "Azure Resource Graph authentication failed (%s).", type(exc).__name__
        )
        raise OpsAssistantUpstreamError(
            "Azure resource monitoring could not authenticate."
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Azure Resource Graph request failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "Azure resource monitoring is temporarily unavailable."
        ) from exc
    finally:
        credential.close()


def get_azure_resource_inventory() -> list[OpsResource]:
    subscription_id = _configured_subscription_id()
    query = (
        "Resources "
        f"| where subscriptionId =~ '{subscription_id}' "
        "| project id, name, type, resourceGroup, location "
        "| order by resourceGroup asc, type asc, name asc"
    )
    rows = _resource_graph_query(query)
    return [
        OpsResource(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            resource_group=row["resourceGroup"],
            location=row.get("location"),
        )
        for row in rows
        if isinstance(row, dict)
        and all(
            isinstance(row.get(key), str)
            for key in ("id", "name", "type", "resourceGroup")
        )
    ]


def get_deployment_knowledge() -> str:
    knowledge_path = Path(__file__).parents[1] / "knowledge" / "deployment.md"
    return knowledge_path.read_text(encoding="utf-8")


def _azure_management_get(path: str, params: dict[str, str] | None = None) -> dict:
    if not settings.OPS_AZURE_SUBSCRIPTION_ID:
        raise OpsAssistantNotConfigured("Azure resource monitoring is not configured.")

    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    try:
        access_token = credential.get_token(
            "https://management.azure.com/.default"
        ).token
        response = httpx.get(
            f"https://management.azure.com{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=20.0,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise OpsAssistantUpstreamError(
                "Azure Monitor returned an invalid response."
            )
        return payload
    except AzureError as exc:
        logger.error("Azure Monitor authentication failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "Azure Monitor could not authenticate."
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Azure Monitor request failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "Azure Monitor is temporarily unavailable."
        ) from exc
    except ValueError as exc:
        raise OpsAssistantUpstreamError(
            "Azure Monitor returned an invalid response."
        ) from exc
    finally:
        credential.close()


def get_azure_resource_metrics(resource_id: str, metric_name: str) -> dict:
    subscription_id = _configured_subscription_id()
    normalized_id = resource_id.strip().rstrip("/")
    normalized_lower = normalized_id.lower()
    if (
        len(normalized_id) > 1024
        or not normalized_lower.startswith(f"/subscriptions/{subscription_id.lower()}/")
        or "/providers/" not in normalized_lower
        or any(character in normalized_id for character in ("?", "#", "\r", "\n"))
    ):
        raise OpsAssistantUpstreamError(
            "Metrics are only available for resources in the configured subscription."
        )
    if not metric_name.strip() or len(metric_name) > 160:
        raise OpsAssistantUpstreamError("The metric name is invalid.")

    encoded_id = quote(normalized_id, safe="/")
    definitions = _azure_management_get(
        f"{encoded_id}/providers/Microsoft.Insights/metricDefinitions",
        {"api-version": "2018-01-01"},
    ).get("value", [])
    available_metrics = {
        item.get("name", {}).get("value")
        for item in definitions
        if isinstance(item, dict) and isinstance(item.get("name"), dict)
    }
    if metric_name not in available_metrics:
        raise OpsAssistantUpstreamError(
            "That metric is not available for the selected resource."
        )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)
    metrics = _azure_management_get(
        f"{encoded_id}/providers/Microsoft.Insights/metrics",
        {
            "api-version": "2018-01-01",
            "metricnames": metric_name,
            "timespan": (
                f"{start_time.isoformat(timespec='seconds')}/"
                f"{end_time.isoformat(timespec='seconds')}"
            ),
            "interval": "PT15M",
            "aggregation": "Average",
        },
    ).get("value", [])
    metric = metrics[0] if isinstance(metrics, list) and metrics else {}
    series = metric.get("timeseries", []) if isinstance(metric, dict) else []
    recent_series = []
    if isinstance(series, list):
        for item in series[:5]:
            data = item.get("data", []) if isinstance(item, dict) else []
            recent_series.append(
                {"data": data[-4:]} if isinstance(data, list) else {"data": []}
            )
    return {
        "resource_id": normalized_id,
        "metric_name": metric_name,
        "timespan": "Last hour (15-minute intervals)",
        "unit": metric.get("unit") if isinstance(metric, dict) else None,
        "series": recent_series,
    }


def get_azure_resource_health() -> list[OpsResourceHealth]:
    subscription_id = _configured_subscription_id()
    query = (
        "HealthResources "
        "| where type =~ 'microsoft.resourcehealth/availabilitystatuses' "
        "| extend targetResourceId = "
        "tolower(tostring(properties.targetResourceId)) "
        "| join kind=inner (Resources "
        f"| where subscriptionId =~ '{subscription_id}' "
        "| project targetResourceId = tolower(id), name, type, resourceGroup) "
        "on targetResourceId "
        "| project name, type, resourceGroup, "
        "availabilityState = tostring(properties.availabilityState), "
        "reasonType = tostring(properties.reasonType)"
    )
    rows = _resource_graph_query(query)
    return [
        OpsResourceHealth(
            name=row["name"],
            type=row["type"],
            resource_group=row["resourceGroup"],
            availability_state=row["availabilityState"],
            reason_type=row.get("reasonType"),
        )
        for row in rows
        if isinstance(row, dict)
        and all(
            isinstance(row.get(key), str)
            for key in ("name", "type", "resourceGroup", "availabilityState")
        )
    ]


def get_subscription_log_workspaces() -> list[str]:
    subscription_id = _configured_subscription_id()
    rows = _resource_graph_query(
        "Resources "
        "| where type =~ 'microsoft.operationalinsights/workspaces' "
        f"| where subscriptionId =~ '{subscription_id}' "
        "| project workspaceId = tostring(properties.customerId)"
    )
    workspace_ids: set[str] = set()
    for row in rows:
        workspace_id = row.get("workspaceId")
        if not isinstance(workspace_id, str) or not workspace_id:
            continue
        try:
            workspace_ids.add(str(UUID(workspace_id)))
        except ValueError as exc:
            raise OpsAssistantUpstreamError(
                "Azure Resource Graph returned an invalid Log Analytics workspace ID."
            ) from exc
    return sorted(workspace_ids)


def _redact_log_text(value: str) -> str:
    redacted = value
    for pattern in LOG_SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def query_azure_resource_logs(
    workspace_id: str,
    table: str,
    time_range: str,
    filter_field: str | None,
    filter_value: str | None,
    max_results: int,
    credential: Any | None = None,
) -> dict[str, Any]:
    return _query_azure_resource_logs(
        workspace_id=workspace_id,
        table=table,
        time_range=time_range,
        filter_field=filter_field,
        filter_value=filter_value,
        max_results=max_results,
        allowed_workspace_ids=set(get_subscription_log_workspaces()),
        credential=credential,
    )


def _query_azure_resource_logs(
    workspace_id: str,
    table: str,
    time_range: str,
    filter_field: str | None,
    filter_value: str | None,
    max_results: int,
    allowed_workspace_ids: set[str],
    credential: Any | None = None,
) -> dict[str, Any]:
    _configured_subscription_id()
    try:
        normalized_workspace_id = str(UUID(workspace_id))
    except ValueError as exc:
        raise OpsAssistantUpstreamError(
            "The Log Analytics workspace ID is invalid."
        ) from exc
    if normalized_workspace_id not in allowed_workspace_ids:
        raise OpsAssistantUpstreamError(
            "Log queries are only available for workspaces in the configured subscription."
        )
    if table not in LOG_TABLES:
        raise OpsAssistantUpstreamError("That Log Analytics table is not allowed.")
    if time_range not in LOG_TIME_RANGES:
        raise OpsAssistantUpstreamError("That Log Analytics time range is not allowed.")
    if max_results not in (25, 50, 100, MAX_LOG_RESULTS):
        raise OpsAssistantUpstreamError("The requested log result limit is invalid.")

    table_config = LOG_TABLES[table]
    subscription_id = _configured_subscription_id()
    if table_config["scope_type"] == "subscription_id":
        scope_filter = (
            f"tolower(tostring({table_config['scope_field']})) "
            f"== '{subscription_id.lower()}'"
        )
    else:
        scope_filter = (
            f"tostring({table_config['scope_field']}) "
            f"startswith '/subscriptions/{subscription_id}/'"
        )
    query_lines = [
        table,
        f"| where TimeGenerated >= ago({LOG_TIME_RANGES[time_range]['kql']})",
        f"| where {scope_filter}",
    ]
    if filter_field is not None or filter_value is not None:
        if (
            filter_field not in table_config["filter_fields"]
            or not isinstance(filter_value, str)
            or not filter_value.strip()
            or len(filter_value) > 128
            or any(ord(character) < 32 for character in filter_value)
        ):
            raise OpsAssistantUpstreamError(
                "The log filter is invalid for the selected table."
            )
        escaped_filter = filter_value.replace("'", "''")
        query_lines.append(
            f"| where tostring({filter_field}) contains '{escaped_filter}'"
        )
    query_lines.extend(
        [
            "| project " + ", ".join(table_config["columns"]),
            "| order by TimeGenerated desc",
            f"| take {max_results + 1}",
        ]
    )

    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential

    owns_credential = credential is None
    if owns_credential:
        credential = DefaultAzureCredential()
    try:
        token = credential.get_token("https://api.loganalytics.io/.default").token
        response = httpx.post(
            f"https://api.loganalytics.io/v1/workspaces/{normalized_workspace_id}/query",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"query": "\n".join(query_lines)},
            params={"timespan": LOG_TIME_RANGES[time_range]["timespan"]},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        tables = payload.get("tables") if isinstance(payload, dict) else None
        if not isinstance(tables, list) or not tables:
            raise OpsAssistantUpstreamError(
                "Log Analytics returned an invalid response."
            )
        result_table = tables[0]
        columns = (
            result_table.get("columns") if isinstance(result_table, dict) else None
        )
        rows = result_table.get("rows") if isinstance(result_table, dict) else None
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise OpsAssistantUpstreamError(
                "Log Analytics returned an invalid response."
            )
        column_names = [
            column.get("name")
            for column in columns
            if isinstance(column, dict) and isinstance(column.get("name"), str)
        ]
        if len(column_names) != len(columns) or any(
            not isinstance(row, list) or len(row) != len(column_names)
            for row in rows[: max_results + 1]
        ):
            raise OpsAssistantUpstreamError(
                "Log Analytics returned an invalid response."
            )
        records = []
        response_characters = 0
        for row in rows[:max_results]:
            record = dict(zip(column_names, row, strict=True))
            record = {
                key: (
                    (
                        _redact_log_text(value[:2048])
                        + (" [truncated]" if len(value) > 2048 else "")
                    )
                    if isinstance(value, str)
                    else value
                )
                for key, value in record.items()
            }
            record_size = len(json.dumps(record, default=str))
            if response_characters + record_size > MAX_LOG_RESPONSE_CHARACTERS:
                break
            records.append(record)
            response_characters += record_size
        is_truncated = len(rows) > max_results or len(records) < min(
            len(rows), max_results
        )
        return {
            "workspace_id": normalized_workspace_id,
            "table": table,
            "time_range": time_range,
            "result_count": len(records),
            "max_results": max_results,
            "truncated": is_truncated,
            "records": records,
        }
    except AzureError as exc:
        logger.error("Log Analytics authentication failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "Log Analytics could not authenticate."
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Log Analytics request failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "Log Analytics is temporarily unavailable."
        ) from exc
    except ValueError as exc:
        raise OpsAssistantUpstreamError(
            "Log Analytics returned an invalid response."
        ) from exc
    finally:
        if owns_credential:
            credential.close()


def get_azure_ops_alerts() -> OpsAssistantAlertsResponse:
    alerts = []
    unavailable_sources: set[str] = set()
    for health in get_azure_resource_health():
        state = health.availability_state.lower()
        if state not in ("degraded", "unavailable"):
            continue
        alerts.append(
            OpsAssistantAlert(
                id=f"health:{health.resource_group}:{health.name}:{state}",
                source="Azure Resource Health",
                severity="critical" if state == "unavailable" else "warning",
                title=f"Resource health is {state}",
                resource_name=health.name,
                scope=health.resource_group,
                summary=f"Azure Resource Health reported {health.availability_state}.",
            )
        )

    workspace_ids = get_subscription_log_workspaces()
    if not workspace_ids:
        return OpsAssistantAlertsResponse(
            checked_at=datetime.now(timezone.utc).isoformat(),
            alerts=alerts,
            unavailable_sources=[
                "No Log Analytics workspaces were found in the configured subscription."
            ],
        )

    from azure.identity import DefaultAzureCredential

    alert_queries = (
        (
            "AzureActivity",
            "ActivityStatusValue",
            "Failed",
            "Azure Activity",
            "Azure operation failed",
            "error",
        ),
        (
            "AzureDiagnostics",
            "Level",
            "Error",
            "Azure Diagnostics",
            "Azure diagnostic error",
            "error",
        ),
        (
            "KubeEvents",
            "KubeEventType",
            "Warning",
            "AKS events",
            "AKS warning event",
            "warning",
        ),
        (
            "ContainerLogV2",
            "LogLevel",
            "Error",
            "AKS container logs",
            "AKS container error",
            "error",
        ),
    )
    credential = DefaultAzureCredential()
    try:
        for workspace_id in workspace_ids:
            for (
                table,
                filter_field,
                filter_value,
                source,
                title,
                severity,
            ) in alert_queries:
                try:
                    result = _query_azure_resource_logs(
                        workspace_id=workspace_id,
                        table=table,
                        time_range="15m",
                        filter_field=filter_field,
                        filter_value=filter_value,
                        max_results=25,
                        allowed_workspace_ids=set(workspace_ids),
                        credential=credential,
                    )
                except OpsAssistantUpstreamError as exc:
                    logger.warning(
                        "Ops alert source query failed for %s (%s).",
                        source,
                        type(exc).__name__,
                    )
                    unavailable_sources.add(f"{source} ({workspace_id[-6:]})")
                    continue
                if result["truncated"]:
                    unavailable_sources.add(
                        f"Some {source} results were omitted by the response cap."
                    )
                for record in result["records"]:
                    occurred_at = record.get("TimeGenerated")
                    resource_id = record.get("ResourceId")
                    if not isinstance(resource_id, str):
                        resource_id = ""
                    if source == "Azure Activity":
                        resource_name = resource_id.rstrip("/").split("/")[-1] or None
                        scope = _resource_group_from_id(resource_id)
                        identifier = (
                            f"activity:{workspace_id}:{occurred_at}:"
                            f"{resource_id}:{record.get('OperationNameValue')}"
                        )
                        operation = record.get("OperationNameValue")
                        summary = "Azure Activity reported a failed operation" + (
                            f": {_redact_log_text(operation[:160])}"
                            if isinstance(operation, str)
                            else "."
                        )
                    elif source == "AKS events":
                        resource_name = record.get("Name")
                        namespace = record.get("Namespace")
                        scope = namespace if isinstance(namespace, str) else None
                        identifier = (
                            f"kube-event:{workspace_id}:{occurred_at}:"
                            f"{namespace}:{resource_name}:{record.get('Reason')}"
                        )
                        summary = "Kubernetes reported a warning event."
                    elif source == "AKS container logs":
                        resource_name = record.get("PodName")
                        namespace = record.get("PodNamespace")
                        scope = namespace if isinstance(namespace, str) else None
                        identifier = (
                            f"container-log:{workspace_id}:{occurred_at}:"
                            f"{namespace}:{resource_name}:{record.get('ContainerName')}"
                        )
                        summary = "Container logs reported an error-level entry."
                    else:
                        resource_name = record.get("Resource")
                        scope = _resource_group_from_id(resource_id)
                        identifier = (
                            f"diagnostic:{workspace_id}:{occurred_at}:"
                            f"{resource_id}:{record.get('Category')}:"
                            f"{record.get('OperationName')}"
                        )
                        summary = "Azure diagnostics reported an error-level entry."
                    alerts.append(
                        OpsAssistantAlert(
                            id=identifier[:512],
                            source=source,
                            severity=severity,
                            title=title,
                            resource_name=(
                                resource_name
                                if isinstance(resource_name, str)
                                else None
                            ),
                            scope=scope,
                            occurred_at=(
                                occurred_at if isinstance(occurred_at, str) else None
                            ),
                            summary=summary,
                        )
                    )
    finally:
        credential.close()
    ordered_alerts = sorted(
        alerts,
        key=lambda alert: alert.occurred_at or "",
        reverse=True,
    )
    if len(ordered_alerts) > 200:
        unavailable_sources.add(
            "Some active alert results were omitted by the response cap."
        )
    return OpsAssistantAlertsResponse(
        checked_at=datetime.now(timezone.utc).isoformat(),
        alerts=ordered_alerts[:200],
        unavailable_sources=sorted(unavailable_sources),
    )


def _resource_group_from_id(resource_id: str) -> str | None:
    segments = resource_id.split("/")
    for index, segment in enumerate(segments[:-1]):
        if segment.lower() == "resourcegroups":
            return segments[index + 1]
    return None


def _call_azure_function_tool(name: str, arguments: dict[str, Any]) -> str:
    base_url = settings.OPS_ASSISTANT_FUNCTIONS_BASE_URL
    function_key = settings.OPS_ASSISTANT_FUNCTIONS_KEY
    route = FUNCTION_TOOL_ROUTES.get(name)
    if not base_url or not function_key or not route:
        return json.dumps(
            {"error": "Azure Functions tools are not configured for this deployment."}
        )

    normalized_base_url = base_url.rstrip("/")
    if not normalized_base_url.startswith("https://"):
        return json.dumps(
            {"error": "Azure Functions tools must use an HTTPS endpoint."}
        )
    try:
        response = httpx.post(
            f"{normalized_base_url}/{route}",
            headers={"x-functions-key": function_key},
            json=arguments,
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        logger.error(
            "Azure Functions tool request failed for %s (%s).",
            name,
            type(exc).__name__,
        )
        return json.dumps(
            {"error": "The Azure Functions tool is temporarily unavailable."}
        )
    except ValueError:
        logger.error("Azure Functions tool returned invalid JSON for %s.", name)
        return json.dumps(
            {"error": "The Azure Functions tool returned an invalid response."}
        )
    return json.dumps(payload)


def _tool_arguments_error(name: str, parsed_arguments: Any) -> str | None:
    if name in (
        "get_azure_resource_inventory",
        "get_azure_resource_health",
        "get_subscription_log_workspaces",
    ):
        if parsed_arguments != {}:
            return "This tool does not accept arguments."
    elif name == "query_azure_resource_logs":
        required_keys = {
            "workspace_id",
            "table",
            "time_range",
            "filter_field",
            "filter_value",
            "max_results",
        }
        if (
            not isinstance(parsed_arguments, dict)
            or set(parsed_arguments) != required_keys
            or not isinstance(parsed_arguments["workspace_id"], str)
            or not isinstance(parsed_arguments["table"], str)
            or not isinstance(parsed_arguments["time_range"], str)
            or (
                parsed_arguments["filter_field"] is not None
                and not isinstance(parsed_arguments["filter_field"], str)
            )
            or (
                parsed_arguments["filter_value"] is not None
                and not isinstance(parsed_arguments["filter_value"], str)
            )
            or not isinstance(parsed_arguments["max_results"], int)
            or isinstance(parsed_arguments["max_results"], bool)
        ):
            return "Log query arguments were invalid."
    elif name == "get_azure_resource_metrics":
        if (
            not isinstance(parsed_arguments, dict)
            or set(parsed_arguments) != {"resource_id", "metric_name"}
            or not all(isinstance(value, str) for value in parsed_arguments.values())
        ):
            return "Metric query arguments were invalid."
    else:
        return "Requested tool is not available."
    return None


def _execute_local_tool(name: str, parsed_arguments: dict[str, Any]) -> str:
    validation_error = _tool_arguments_error(name, parsed_arguments)
    if validation_error:
        return json.dumps({"error": validation_error})
    try:
        if name == "get_azure_resource_inventory":
            return json.dumps(
                [resource.model_dump() for resource in get_azure_resource_inventory()]
            )
        if name == "get_azure_resource_health":
            return json.dumps(
                [resource.model_dump() for resource in get_azure_resource_health()]
            )
        if name == "get_azure_resource_metrics":
            return json.dumps(
                get_azure_resource_metrics(
                    parsed_arguments["resource_id"],
                    parsed_arguments["metric_name"],
                )
            )
        if name == "get_subscription_log_workspaces":
            return json.dumps(get_subscription_log_workspaces())
        if name == "query_azure_resource_logs":
            return json.dumps(query_azure_resource_logs(**parsed_arguments))
    except OpsAssistantNotConfigured:
        return json.dumps(
            {
                "error": "Azure resource monitoring is not configured for this deployment."
            }
        )
    except OpsAssistantUpstreamError as exc:
        return json.dumps({"error": str(exc)})
    return json.dumps({"error": "Requested tool is not available."})


def _execute_tool(name: str, arguments: str) -> str:
    try:
        parsed_arguments = json.loads(arguments)
    except json.JSONDecodeError:
        return json.dumps({"error": "Tool arguments were invalid."})
    if not isinstance(parsed_arguments, dict):
        return json.dumps({"error": "Tool arguments were invalid."})
    validation_error = _tool_arguments_error(name, parsed_arguments)
    if validation_error:
        return json.dumps({"error": validation_error})

    return _call_azure_function_tool(name, parsed_arguments)


def _run_foundry_response(messages: list[OpsAssistantMessage]) -> str:
    endpoint = settings.FOUNDRY_PROJECT_ENDPOINT
    agent_name = settings.FOUNDRY_AGENT_NAME
    if not endpoint or not agent_name:
        raise OpsAssistantNotConfigured(
            "The Microsoft Foundry agent is not configured."
        )

    from azure.ai.projects import AIProjectClient
    from azure.core.exceptions import AzureError
    from azure.identity import DefaultAzureCredential
    from openai import APIError, OpenAIError

    input_messages = [
        {"type": "message", "role": "developer", "content": AGENT_POLICY},
        {
            "type": "message",
            "role": "developer",
            "content": f"Curated EITOAP deployment reference:\n{get_deployment_knowledge()}",
        },
        *[{"type": "message", **message.model_dump()} for message in messages],
    ]
    credential = DefaultAzureCredential()
    try:
        with AIProjectClient(
            endpoint=endpoint, credential=credential, allow_preview=True
        ) as project_client:
            with project_client.get_openai_client(
                agent_name=agent_name
            ) as openai_client:
                response = openai_client.responses.create(
                    input=input_messages,
                    max_output_tokens=1500,
                )
                for _ in range(MAX_TOOL_ROUNDS):
                    tool_calls = [
                        item for item in response.output if item.type == "function_call"
                    ]
                    if not tool_calls:
                        break
                    tool_outputs = [
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": _execute_tool(call.name, call.arguments),
                        }
                        for call in tool_calls
                    ]
                    response = openai_client.responses.create(
                        input=tool_outputs,
                        previous_response_id=response.id,
                        max_output_tokens=1500,
                    )
                answer = response.output_text
                if not answer or not answer.strip():
                    raise OpsAssistantUpstreamError(
                        "Microsoft Foundry returned an empty response."
                    )
                return answer.strip()
    except (AzureError, APIError, OpenAIError) as exc:
        logger.error("Microsoft Foundry request failed (%s).", type(exc).__name__)
        raise OpsAssistantUpstreamError(
            "The Microsoft Foundry assistant is temporarily unavailable."
        ) from exc
    finally:
        credential.close()


async def ask_ops_assistant(
    messages: list[OpsAssistantMessage],
) -> str:
    from starlette.concurrency import run_in_threadpool

    try:
        return await run_in_threadpool(_run_foundry_response, messages)
    except OpsAssistantNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OpsAssistantUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
