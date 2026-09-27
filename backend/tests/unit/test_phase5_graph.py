from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services.graph_service import GraphAPIException, GraphService


class MockGraphResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class MockGraphClient:
    def __init__(self, methods: list[dict], delete_status: int = 204):
        self.methods = methods
        self.delete_status = delete_status
        self.deleted_urls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, _url: str, headers: dict[str, str]):
        assert headers["Authorization"] == "Bearer test-token"
        return MockGraphResponse(200, {"value": self.methods})

    async def delete(self, url: str, headers: dict[str, str]):
        assert headers["Authorization"] == "Bearer test-token"
        self.deleted_urls.append(url)
        return MockGraphResponse(self.delete_status)


def configure_real_graph(monkeypatch):
    monkeypatch.setattr(settings, "ENTRA_CLIENT_ID", "test-client")
    monkeypatch.setattr(settings, "ENTRA_TENANT_ID", "test-tenant")


@pytest.mark.asyncio
async def test_graph_mfa_reset_deletes_registered_non_password_methods(monkeypatch):
    configure_real_graph(monkeypatch)
    graph_client = MockGraphClient(
        [
            {
                "@odata.type": "#microsoft.graph.phoneAuthenticationMethod",
                "id": "phone-method",
            },
            {
                "@odata.type": "#microsoft.graph.passwordAuthenticationMethod",
                "id": "password-method",
            },
        ]
    )
    monkeypatch.setattr(
        "app.services.graph_service.httpx.AsyncClient",
        lambda **_kwargs: graph_client,
    )
    service = GraphService()
    monkeypatch.setattr(
        service, "get_access_token", AsyncMock(return_value="test-token")
    )

    removed = await service.reset_mfa_methods("employee@example.com")

    assert removed == 1
    assert len(graph_client.deleted_urls) == 1
    assert graph_client.deleted_urls[0].endswith(
        "/authentication/phoneMethods/phone-method"
    )


@pytest.mark.asyncio
async def test_graph_mfa_reset_surfaces_safe_graph_failure(monkeypatch):
    configure_real_graph(monkeypatch)
    graph_client = MockGraphClient([], delete_status=403)

    async def fail_lookup(_url: str, headers: dict[str, str]):
        assert headers["Authorization"] == "Bearer test-token"
        return MockGraphResponse(403, {"error": {"message": "private Graph detail"}})

    graph_client.get = fail_lookup
    monkeypatch.setattr(
        "app.services.graph_service.httpx.AsyncClient",
        lambda **_kwargs: graph_client,
    )
    service = GraphService()
    monkeypatch.setattr(
        service, "get_access_token", AsyncMock(return_value="test-token")
    )

    with pytest.raises(GraphAPIException) as error:
        await service.reset_mfa_methods("employee@example.com")

    assert error.value.status_code == 502
    assert "private Graph detail" not in error.value.message


@pytest.mark.asyncio
async def test_graph_mfa_reset_refuses_unsupported_method_without_deleting(
    monkeypatch,
):
    configure_real_graph(monkeypatch)
    graph_client = MockGraphClient(
        [{"@odata.type": "#microsoft.graph.unrecognizedMethod", "id": "method-id"}]
    )
    monkeypatch.setattr(
        "app.services.graph_service.httpx.AsyncClient",
        lambda **_kwargs: graph_client,
    )
    service = GraphService()
    monkeypatch.setattr(
        service, "get_access_token", AsyncMock(return_value="test-token")
    )

    with pytest.raises(GraphAPIException):
        await service.reset_mfa_methods("employee@example.com")

    assert graph_client.deleted_urls == []
