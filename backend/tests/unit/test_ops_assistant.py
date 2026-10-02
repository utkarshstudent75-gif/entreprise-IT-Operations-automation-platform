import json

import pytest
from pydantic import ValidationError

from app.main import _ops_assistant_allowed_origins
from app.schemas.ops_assistant import OpsAssistantChatRequest, OpsResource
from app.services import ops_assistant_service as service


def test_chat_request_requires_latest_user_message():
    with pytest.raises(ValidationError):
        OpsAssistantChatRequest(
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
        )


def test_chat_request_limits_total_conversation_size():
    with pytest.raises(ValidationError):
        OpsAssistantChatRequest(
            messages=[
                {"role": "user", "content": "x" * 4000},
                {"role": "assistant", "content": "x" * 4000},
                {"role": "user", "content": "x" * 4001},
            ]
        )


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


def test_resource_graph_inventory_is_limited_to_configured_groups(monkeypatch):
    observed_queries = []

    def fake_query(query):
        observed_queries.append(query)
        return [
            {
                "id": "/subscriptions/example/resourceGroups/enterprise-it-operations-platform-dev-rg/providers/Microsoft.Compute/virtualMachines/app",
                "name": "app",
                "type": "Microsoft.Compute/virtualMachines",
                "resourceGroup": "enterprise-it-operations-platform-dev-rg",
                "location": "eastus",
                "properties": {"sensitive": "not projected"},
            }
        ]

    monkeypatch.setattr(service, "_resource_graph_query", fake_query)
    resources = service.get_azure_resource_inventory()

    assert len(resources) == 1
    assert resources[0] == OpsResource(
        id="/subscriptions/example/resourceGroups/enterprise-it-operations-platform-dev-rg/providers/Microsoft.Compute/virtualMachines/app",
        name="app",
        type="Microsoft.Compute/virtualMachines",
        resource_group="enterprise-it-operations-platform-dev-rg",
        location="eastus",
    )
    assert "eitoap-tfstate-rg" in observed_queries[0]
    assert (
        "mc_enterprise-it-operations-platform-dev-rg_enterprise-dev-aks_eastus"
        in observed_queries[0]
    )
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


def test_metrics_reject_resource_ids_outside_configured_groups(monkeypatch):
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", "subscription-1")
    monkeypatch.setattr(
        service,
        "_azure_management_get",
        lambda *_args, **_kwargs: pytest.fail("Must not query an unapproved resource"),
    )

    with pytest.raises(service.OpsAssistantUpstreamError):
        service.get_azure_resource_metrics(
            "/subscriptions/other/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/vm",
            "Percentage CPU",
        )


def test_metrics_require_a_metric_advertised_for_the_resource(monkeypatch):
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", "subscription-1")
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
            "/subscriptions/subscription-1/resourceGroups/eitoap-tfstate-rg/providers/Microsoft.Compute/virtualMachines/vm",
            "SecretValue",
        )

    assert len(calls) == 1
    assert calls[0][0].endswith("/metricDefinitions")


def test_metrics_return_only_a_bounded_recent_sample(monkeypatch):
    monkeypatch.setattr(service.settings, "OPS_AZURE_SUBSCRIPTION_ID", "subscription-1")
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
        "/subscriptions/subscription-1/resourceGroups/eitoap-tfstate-rg/providers/Microsoft.Compute/virtualMachines/vm",
        "Percentage CPU",
    )

    assert calls[1][1]["interval"] == "PT15M"
    assert len(metric["series"]) == 5
    assert metric["series"][0]["data"] == [{"average": point} for point in range(6, 10)]


def test_deployment_knowledge_is_packaged_with_backend():
    knowledge = service.get_deployment_knowledge()

    assert "Argo CD" in knowledge
    assert "eitoap-tfstate-rg" in knowledge
    assert "never read Terraform state blobs" in knowledge
