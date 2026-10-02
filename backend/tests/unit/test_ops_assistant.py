import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routers import ops_assistant as ops_assistant_router
from app.api.routers.ops_assistant import _check_assistant_rate_limit
from app.core.exceptions import RateLimitExceededException
from app.core.rate_limiter import rate_limiter
from app.main import _ops_assistant_allowed_origins
from app.schemas.ops_assistant import (
    OpsAssistantAlertEvent,
    OpsAssistantChatRequest,
    OpsResource,
    OpsResourceHealth,
)
from app.services import ops_assistant_service as service


def test_chat_request_requires_latest_user_message():
    with pytest.raises(ValidationError):
        OpsAssistantChatRequest(
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
        )


def test_chat_request_accepts_bounded_assistant_context_before_latest_user():
    request = OpsAssistantChatRequest(
        messages=[
            {"role": "user", "content": "List the VMs"},
            {"role": "assistant", "content": "I found two virtual machines."},
            {"role": "user", "content": "Check the first VM's health"},
        ]
    )

    assert request.messages[-1].content == "Check the first VM's health"


def test_chat_request_allows_longer_but_bounded_assistant_context():
    request = OpsAssistantChatRequest(
        messages=[
            {"role": "assistant", "content": "x" * 5000},
            {"role": "user", "content": "Summarize that result"},
        ]
    )

    assert len(request.messages[0].content) == 5000


def test_chat_request_limits_total_conversation_size():
    with pytest.raises(ValidationError):
        OpsAssistantChatRequest(
            messages=[
                {"role": "user", "content": "x" * 4000},
                {"role": "assistant", "content": "x" * 4000},
                {"role": "user", "content": "x" * 4001},
            ]
        )


def test_assistant_rate_limit_returns_retryable_http_error(monkeypatch):
    def exceed_limit(**_kwargs):
        raise RateLimitExceededException()

    monkeypatch.setattr(rate_limiter, "check_limit", exceed_limit)

    with pytest.raises(HTTPException) as error:
        _check_assistant_rate_limit(
            {"email": "operator@example.com"},
            "alerts",
            5,
        )

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == "60"


def test_assistant_cors_requires_explicit_https_origins(monkeypatch):
    monkeypatch.setattr(
        service.settings,
        "OPS_ASSISTANT_ALLOWED_ORIGINS",
        " https://assistant.example.com/,https://ops.example.com ",
    )

    assert _ops_assistant_allowed_origins() == [
        "https://assistant.example.com",
        "https://ops.example.com",
    ]


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "http://assistant.example.com",
        "https://assistant.example.com/path",
        "https://user:password@assistant.example.com",
    ],
)
def test_assistant_cors_rejects_unsafe_origins(monkeypatch, origin):
    monkeypatch.setattr(service.settings, "OPS_ASSISTANT_ALLOWED_ORIGINS", origin)

    with pytest.raises(ValueError, match="explicit HTTPS origins"):
        _ops_assistant_allowed_origins()


def test_resource_graph_inventory_is_limited_to_configured_subscription(monkeypatch):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    observed_queries = []

    def fake_query(query):
        observed_queries.append(query)
        return [
            {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/example/providers/Microsoft.Compute/virtualMachines/app",
                "name": "app",
                "type": "Microsoft.Compute/virtualMachines",
                "resourceGroup": "example",
                "location": "eastus",
                "properties": {"sensitive": "not projected"},
            }
        ]

    monkeypatch.setattr(service, "_resource_graph_query", fake_query)
    resources = service.get_azure_resource_inventory()

    assert len(resources) == 1
    assert resources[0] == OpsResource(
        id=f"/subscriptions/{subscription_id}/resourceGroups/example/providers/Microsoft.Compute/virtualMachines/app",
        name="app",
        type="Microsoft.Compute/virtualMachines",
        resource_group="example",
        location="eastus",
    )
    assert f"subscriptionId =~ '{subscription_id}'" in observed_queries[0]
    assert "where tolower(resourceGroup)" not in observed_queries[0]
    assert "properties" not in observed_queries[0]
    assert "Microsoft.Resources/deployments" not in observed_queries[0]


def test_function_tool_rejects_unexpected_arguments():
    result = json.loads(
        service._execute_tool(
            "get_azure_resource_inventory",
            '{"resource_group": "attacker-controlled"}',
        )
    )

    assert result == {"error": "This tool does not accept arguments."}


def test_function_tool_does_not_execute_unregistered_operations():
    result = json.loads(service._execute_tool("run_shell", "{}"))

    assert result == {"error": "Requested tool is not available."}


def test_assistant_tool_calls_its_configured_azure_function(monkeypatch):
    monkeypatch.setattr(
        service.settings,
        "OPS_ASSISTANT_FUNCTIONS_BASE_URL",
        "https://ops-functions.azurewebsites.net/api/",
    )
    monkeypatch.setattr(service.settings, "OPS_ASSISTANT_FUNCTIONS_KEY", "test-key")
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"id": "/subscriptions/example/resourceGroups/rg"}]

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(service.httpx, "post", fake_post)
    result = json.loads(service._execute_tool("get_azure_resource_inventory", "{}"))

    assert result == [{"id": "/subscriptions/example/resourceGroups/rg"}]
    assert calls[0][0] == "https://ops-functions.azurewebsites.net/api/tools/inventory"
    assert calls[0][1]["headers"] == {"x-functions-key": "test-key"}
    assert calls[0][1]["json"] == {}


def test_alert_event_requires_a_valid_shared_ingest_token(monkeypatch):
    monkeypatch.setattr(
        ops_assistant_router.settings,
        "OPS_ASSISTANT_ALERT_INGEST_TOKEN",
        "expected-token",
    )
    event = OpsAssistantAlertEvent(
        condition="fired",
        alert={
            "id": "alert-1",
            "source": "Azure Monitor",
            "severity": "warning",
            "title": "CPU high",
            "summary": "Azure Monitor detected high CPU.",
        },
    )

    with pytest.raises(HTTPException) as error:
        import asyncio

        asyncio.run(ops_assistant_router.ingest_monitor_alert(event, "wrong-token"))

    assert error.value.status_code == 401


def test_alert_event_is_stored_and_published_to_redis(monkeypatch):
    import asyncio

    monkeypatch.setattr(
        ops_assistant_router.settings,
        "OPS_ASSISTANT_ALERT_INGEST_TOKEN",
        "expected-token",
    )
    calls = []

    class FakeRedis:
        async def hset(self, *args):
            calls.append(("hset", args))

        async def expire(self, *args):
            calls.append(("expire", args))

        async def publish(self, *args):
            calls.append(("publish", args))

    async def fake_get_redis():
        return FakeRedis()

    monkeypatch.setattr(ops_assistant_router, "get_redis", fake_get_redis)
    event = OpsAssistantAlertEvent(
        condition="fired",
        alert={
            "id": "alert-1",
            "source": "Azure Monitor",
            "severity": "critical",
            "title": "Resource unavailable",
            "summary": "Azure Resource Health reported unavailable.",
        },
    )

    result = asyncio.run(
        ops_assistant_router.ingest_monitor_alert(event, "expected-token")
    )

    assert result == {"accepted": True}
    assert calls[0][0] == "hset"
    assert calls[1] == ("expire", (ops_assistant_router.ACTIVE_ALERTS_KEY, 604800))
    assert calls[2][0] == "publish"
    assert json.loads(calls[2][1][1])["condition"] == "fired"


def test_azure_monitor_function_normalizes_alerts_and_redacts_secrets():
    from function_app import _normalize_monitor_alert

    payload = {
        "schemaId": "azureMonitorCommonAlertSchema",
        "data": {
            "essentials": {
                "alertId": "alert-1",
                "monitorCondition": "Fired",
                "severity": "Sev1",
                "alertRule": "API availability degraded",
                "alertTargetIDs": [
                    "/subscriptions/sub/resourceGroups/app/providers/Microsoft.Web/sites/api"
                ],
                "firedDateTime": "2026-10-02T12:00:00Z",
                "description": "Connection failed; token=private-value",
            }
        },
    }

    event = _normalize_monitor_alert(payload)

    assert event["condition"] == "fired"
    assert event["alert"]["severity"] == "critical"
    assert event["alert"]["resource_name"] == "api"
    assert event["alert"]["scope"] == "app"
    assert "[REDACTED]" in event["alert"]["summary"]
    assert "private-value" not in event["alert"]["summary"]


def test_azure_functions_http_bindings_match_python_request_parameters():
    from function_app import app

    functions = app.get_functions()

    assert len(functions) == 6
    for function in functions:
        bindings = json.loads(function.get_function_json())["bindings"]
        trigger = next(
            binding for binding in bindings if binding["type"] == "httpTrigger"
        )
        assert trigger["name"] == "req"


def test_metrics_reject_resource_ids_outside_configured_groups(monkeypatch):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setattr(
        service,
        "_azure_management_get",
        lambda *_args, **_kwargs: pytest.fail("Must not query an unapproved resource"),
    )

    with pytest.raises(service.OpsAssistantUpstreamError):
        service.get_azure_resource_metrics(
            "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/vm",
            "Percentage CPU",
        )


def test_metrics_require_a_metric_advertised_for_the_resource(monkeypatch):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    calls = []

    def fake_management_get(path, params=None):
        calls.append((path, params))
        return {
            "value": [
                {"name": {"value": "Percentage CPU"}},
            ]
        }

    monkeypatch.setattr(service, "_azure_management_get", fake_management_get)

    with pytest.raises(service.OpsAssistantUpstreamError):
        service.get_azure_resource_metrics(
            f"/subscriptions/{subscription_id}/resourceGroups/example/providers/Microsoft.Compute/virtualMachines/vm",
            "SecretValue",
        )

    assert len(calls) == 1
    assert calls[0][0].endswith("/metricDefinitions")


def test_metrics_return_only_a_bounded_recent_sample(monkeypatch):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    calls = []

    def fake_management_get(path, params=None):
        calls.append((path, params))
        if path.endswith("/metricDefinitions"):
            return {"value": [{"name": {"value": "Percentage CPU"}}]}
        return {
            "value": [
                {
                    "unit": "Percent",
                    "timeseries": [
                        {"data": [{"average": point} for point in range(10)]}
                        for _ in range(8)
                    ],
                }
            ]
        }

    monkeypatch.setattr(service, "_azure_management_get", fake_management_get)
    metric = service.get_azure_resource_metrics(
        f"/subscriptions/{subscription_id}/resourceGroups/example/providers/Microsoft.Compute/virtualMachines/vm",
        "Percentage CPU",
    )

    assert calls[1][1]["interval"] == "PT15M"
    assert len(metric["series"]) == 5
    assert metric["series"][0]["data"] == [{"average": point} for point in range(6, 10)]


def test_log_query_rejects_workspaces_outside_the_configured_subscription(monkeypatch):
    monkeypatch.setattr(
        service.settings,
        "OPS_AZURE_SUBSCRIPTION_ID",
        "00000000-0000-0000-0000-000000000001",
    )
    monkeypatch.setattr(
        service,
        "_resource_graph_query",
        lambda _query: [{"workspaceId": "00000000-0000-0000-0000-000000000010"}],
    )

    with pytest.raises(
        service.OpsAssistantUpstreamError, match="configured subscription"
    ):
        service.query_azure_resource_logs(
            "00000000-0000-0000-0000-000000000011",
            "ContainerLogV2",
            "1h",
            None,
            None,
            25,
        )


def test_log_workspace_discovery_rejects_invalid_workspace_guids(monkeypatch):
    monkeypatch.setattr(
        service.settings,
        "OPS_AZURE_SUBSCRIPTION_ID",
        "00000000-0000-0000-0000-000000000001",
    )
    monkeypatch.setattr(
        service,
        "_resource_graph_query",
        lambda _query: [{"workspaceId": "bad-workspace-id"}],
    )

    with pytest.raises(
        service.OpsAssistantUpstreamError, match="invalid Log Analytics workspace ID"
    ):
        service.get_subscription_log_workspaces()


def test_log_workspace_discovery_is_scoped_to_the_configured_subscription(
    monkeypatch,
):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    workspace_id = "00000000-0000-0000-0000-000000000010"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    queries = []

    def fake_resource_graph_query(query):
        queries.append(query)
        return [{"workspaceId": workspace_id}]

    monkeypatch.setattr(service, "_resource_graph_query", fake_resource_graph_query)

    assert service.get_subscription_log_workspaces() == [workspace_id]
    assert f"subscriptionId =~ '{subscription_id}'" in queries[0]
    assert "microsoft.operationalinsights/workspaces" in queries[0]


def test_log_query_uses_only_curated_kql_and_bounded_arguments(monkeypatch):
    from azure.identity import DefaultAzureCredential

    subscription_id = "00000000-0000-0000-0000-000000000001"
    workspace_id = "00000000-0000-0000-0000-000000000010"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setattr(
        service,
        "_resource_graph_query",
        lambda _query: [{"workspaceId": workspace_id}],
    )
    monkeypatch.setattr(
        DefaultAzureCredential,
        "get_token",
        lambda *_args, **_kwargs: type("Token", (), {"token": "test-token"})(),
    )
    monkeypatch.setattr(DefaultAzureCredential, "close", lambda *_args: None)
    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "tables": [
                    {
                        "columns": [
                            {"name": "TimeGenerated"},
                            {"name": "PodNamespace"},
                            {"name": "LogMessage"},
                        ],
                        "rows": [
                            [
                                "2026-10-02T00:00:00Z",
                                "backend",
                                "Authorization: Bearer abc123 password=example",
                            ]
                        ],
                    }
                ]
            }

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(service.httpx, "post", fake_post)
    result = service.query_azure_resource_logs(
        workspace_id,
        "ContainerLogV2",
        "6h",
        "PodNamespace",
        "back'end",
        25,
    )

    assert result["result_count"] == 1
    assert result["records"][0]["TimeGenerated"] == "2026-10-02T00:00:00Z"
    assert result["records"][0]["PodNamespace"] == "backend"
    assert "[REDACTED]" in result["records"][0]["LogMessage"]
    assert "abc123" not in result["records"][0]["LogMessage"]
    assert "example" not in result["records"][0]["LogMessage"]
    request = calls[0][1]
    assert "| where TimeGenerated >= ago(6h)" in request["json"]["query"]
    assert (
        f"| where tostring(_ResourceId) startswith '/subscriptions/{subscription_id}/'"
    ) in request["json"]["query"]
    assert (
        "| where tostring(PodNamespace) contains 'back''end'"
        in request["json"]["query"]
    )
    assert "| take 26" in request["json"]["query"]
    assert request["params"] == {"timespan": "PT6H"}
    assert "https://api.loganalytics.io/v1/workspaces/" in calls[0][0]


def test_activity_log_query_filters_by_subscription_guid(monkeypatch):
    subscription_id = "00000000-0000-0000-0000-000000000001"
    workspace_id = "00000000-0000-0000-0000-000000000010"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    query_text = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "tables": [
                    {
                        "columns": [{"name": "SubscriptionId"}],
                        "rows": [],
                    }
                ]
            }

    def fake_post(_url, **kwargs):
        query_text.append(kwargs["json"]["query"])
        return Response()

    monkeypatch.setattr(
        service,
        "_resource_graph_query",
        lambda _query: [{"workspaceId": workspace_id}],
    )
    monkeypatch.setattr(service.httpx, "post", fake_post)

    service.query_azure_resource_logs(
        workspace_id,
        "AzureActivity",
        "1h",
        None,
        None,
        25,
        credential=type(
            "FakeCredential",
            (),
            {"get_token": lambda *_args: type("Token", (), {"token": "test"})()},
        )(),
    )

    assert f"tolower(tostring(SubscriptionId)) == '{subscription_id}'" in query_text[0]


def test_log_tool_rejects_malformed_arguments():
    result = json.loads(
        service._execute_tool(
            "query_azure_resource_logs",
            json.dumps(
                {
                    "workspace_id": "not-a-guid",
                    "table": "ContainerLogV2",
                    "time_range": "1h",
                    "filter_field": None,
                    "filter_value": None,
                    "max_results": True,
                }
            ),
        )
    )

    assert result == {"error": "Log query arguments were invalid."}


def test_active_alerts_cover_health_and_curated_log_signals(monkeypatch):
    from azure import identity

    subscription_id = "00000000-0000-0000-0000-000000000001"
    workspace_id = "00000000-0000-0000-0000-000000000010"
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", subscription_id)
    monkeypatch.setattr(
        service,
        "get_subscription_log_workspaces",
        lambda: [workspace_id],
    )
    monkeypatch.setattr(
        service,
        "get_azure_resource_health",
        lambda: [
            OpsResourceHealth(
                name="api",
                type="Microsoft.Web/sites",
                resource_group="app-rg",
                availability_state="Degraded",
            ),
            OpsResourceHealth(
                name="database",
                type="Microsoft.DBforPostgreSQL/flexibleServers",
                resource_group="data-rg",
                availability_state="Available",
            ),
        ],
    )

    class FakeCredential:
        def close(self):
            return None

    monkeypatch.setattr(identity, "DefaultAzureCredential", FakeCredential)
    calls = []

    def fake_query(**kwargs):
        calls.append(kwargs)
        table = kwargs["table"]
        rows = {
            "AzureActivity": [
                {
                    "TimeGenerated": "2026-10-02T12:00:00Z",
                    "ResourceId": (
                        f"/subscriptions/{subscription_id}/resourceGroups/app-rg/"
                        "providers/Microsoft.Web/sites/api"
                    ),
                    "OperationNameValue": "Microsoft.Web/sites/restart/action",
                }
            ],
            "AzureDiagnostics": [
                {
                    "TimeGenerated": "2026-10-02T12:00:00Z",
                    "Resource": "api",
                    "ResourceId": (
                        f"/subscriptions/{subscription_id}/resourceGroups/app-rg/"
                        "providers/Microsoft.Web/sites/api"
                    ),
                    "Category": "AppServiceConsoleLogs",
                    "OperationName": "Console",
                }
            ],
            "KubeEvents": [
                {
                    "TimeGenerated": "2026-10-02T12:00:00Z",
                    "Namespace": "backend",
                    "Name": "api-pod",
                    "Reason": "BackOff",
                }
            ],
            "ContainerLogV2": [
                {
                    "TimeGenerated": "2026-10-02T12:00:00Z",
                    "PodNamespace": "backend",
                    "PodName": "api-pod",
                    "ContainerName": "api",
                }
            ],
        }
        return {"records": rows[table], "truncated": False}

    monkeypatch.setattr(service, "_query_azure_resource_logs", fake_query)

    result = service.get_azure_ops_alerts()

    assert len(calls) == 4
    assert all(call["time_range"] == "15m" for call in calls)
    assert {alert.source for alert in result.alerts} == {
        "Azure Resource Health",
        "Azure Activity",
        "Azure Diagnostics",
        "AKS events",
        "AKS container logs",
    }
    assert not result.unavailable_sources


def test_active_alerts_report_unavailable_tables(monkeypatch):
    from azure import identity

    monkeypatch.setattr(
        service.settings,
        "OPS_AZURE_SUBSCRIPTION_ID",
        "00000000-0000-0000-0000-000000000001",
    )
    monkeypatch.setattr(
        service,
        "get_subscription_log_workspaces",
        lambda: ["00000000-0000-0000-0000-000000000010"],
    )
    monkeypatch.setattr(service, "get_azure_resource_health", lambda: [])

    class FakeCredential:
        def close(self):
            return None

    monkeypatch.setattr(identity, "DefaultAzureCredential", FakeCredential)

    def fake_query(**kwargs):
        if kwargs["table"] == "AzureDiagnostics":
            raise service.OpsAssistantUpstreamError("Table not found.")
        return {"records": [], "truncated": False}

    monkeypatch.setattr(service, "_query_azure_resource_logs", fake_query)

    result = service.get_azure_ops_alerts()

    assert result.alerts == []
    assert result.unavailable_sources == ["Azure Diagnostics (000010)"]


def test_deployment_knowledge_is_packaged_with_backend():
    knowledge = service.get_deployment_knowledge()

    assert "Argo CD" in knowledge
    assert "eitoap-tfstate-rg" in knowledge
    assert "never read Terraform state blobs" in knowledge
