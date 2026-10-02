import logging
import os
import re
from typing import Any

import azure.functions as func
import httpx

# Shared backend settings require a database URL; the Functions tool runtime does not use a database.
os.environ.setdefault("DATABASE_URL", "sqlite:///tmp/ops-assistant-functions-unused.db")

from app.services.ops_assistant_service import _execute_local_tool

logger = logging.getLogger("itpa")
app = func.FunctionApp()

ALERT_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key|client[_-]?secret|"
        r"access[_-]?key|connection[_-]?string)([\"']?\s*[:=]\s*[\"']?)([^\"'\s,;]+)"
    ),
)


def _tool_response(request: func.HttpRequest, tool_name: str) -> func.HttpResponse:
    try:
        arguments = request.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON request.", status_code=400)
    if not isinstance(arguments, dict):
        return func.HttpResponse(
            "The request body must be a JSON object.", status_code=400
        )

    result = _execute_local_tool(tool_name, arguments)
    return func.HttpResponse(result, status_code=200, mimetype="application/json")


@app.route(
    route="tools/inventory",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def inventory(req: func.HttpRequest) -> func.HttpResponse:
    return _tool_response(req, "get_azure_resource_inventory")


@app.route(
    route="tools/health",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def resource_health(req: func.HttpRequest) -> func.HttpResponse:
    return _tool_response(req, "get_azure_resource_health")


@app.route(
    route="tools/metrics",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def resource_metrics(req: func.HttpRequest) -> func.HttpResponse:
    return _tool_response(req, "get_azure_resource_metrics")


@app.route(
    route="tools/log-workspaces",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def log_workspaces(req: func.HttpRequest) -> func.HttpResponse:
    return _tool_response(req, "get_subscription_log_workspaces")


@app.route(
    route="tools/logs",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def resource_logs(req: func.HttpRequest) -> func.HttpResponse:
    return _tool_response(req, "query_azure_resource_logs")


def _resource_group_from_id(resource_id: str) -> str | None:
    segments = resource_id.split("/")
    for index, segment in enumerate(segments[:-1]):
        if segment.lower() == "resourcegroups":
            return segments[index + 1]
    return None


def _redact(value: str) -> str:
    result = value
    for pattern in ALERT_SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result[:2048]


def _normalize_monitor_alert(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schemaId") != "azureMonitorCommonAlertSchema":
        raise ValueError("Unsupported Azure Monitor alert schema.")
    data = payload.get("data")
    essentials = data.get("essentials") if isinstance(data, dict) else None
    if not isinstance(essentials, dict):
        raise ValueError("Azure Monitor alert essentials are missing.")

    alert_id = essentials.get("alertId")
    condition = essentials.get("monitorCondition")
    title = essentials.get("alertRule")
    if not all(isinstance(value, str) and value for value in (alert_id, title)):
        raise ValueError("Azure Monitor alert identity is incomplete.")
    if not isinstance(condition, str) or condition.lower() not in ("fired", "resolved"):
        raise ValueError("Azure Monitor alert condition is invalid.")

    severity = essentials.get("severity")
    if not isinstance(severity, str):
        severity = ""
    severity_level = {
        "Sev0": "critical",
        "Sev1": "critical",
        "Sev2": "error",
        "Sev3": "warning",
        "Sev4": "warning",
    }.get(severity, "warning")
    target_ids = essentials.get("alertTargetIDs")
    resource_id = (
        target_ids[0]
        if isinstance(target_ids, list)
        and target_ids
        and isinstance(target_ids[0], str)
        else ""
    )
    description = essentials.get("description")
    summary = description if isinstance(description, str) and description else title
    summary = _redact(summary)
    occurred_at = essentials.get("firedDateTime")
    return {
        "condition": condition.lower(),
        "alert": {
            "id": alert_id[:512],
            "source": "Azure Monitor",
            "severity": severity_level,
            "title": title[:160],
            "resource_name": resource_id.rstrip("/").split("/")[-1] or None,
            "scope": _resource_group_from_id(resource_id) if resource_id else None,
            "occurred_at": occurred_at if isinstance(occurred_at, str) else None,
            "summary": summary,
        },
    }


@app.route(
    route="alerts/monitor",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def monitor_alert(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        if not isinstance(payload, dict):
            raise ValueError("Azure Monitor alert must be a JSON object.")
        event = _normalize_monitor_alert(payload)
    except ValueError as exc:
        logger.warning("Rejected Azure Monitor alert payload (%s).", str(exc))
        return func.HttpResponse(
            "Invalid Azure Monitor alert payload.", status_code=400
        )

    ingest_url = os.getenv("OPS_ASSISTANT_ALERT_INGEST_URL", "")
    ingest_token = os.getenv("OPS_ASSISTANT_ALERT_INGEST_TOKEN", "")
    if not ingest_url or not ingest_token:
        logger.error("Alert ingestion endpoint is not configured.")
        return func.HttpResponse("Alert ingestion is not configured.", status_code=503)
    try:
        response = httpx.post(
            ingest_url,
            headers={"x-ops-alert-token": ingest_token},
            json=event,
            timeout=15.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Alert event forwarding failed (%s).", type(exc).__name__)
        return func.HttpResponse("Alert forwarding failed.", status_code=502)
    return func.HttpResponse(status_code=202)
