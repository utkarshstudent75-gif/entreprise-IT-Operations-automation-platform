import pytest

from app.services.graph_service import GraphAPIException, GraphService


def test_graph_service_mock_mode():
    """Tests that GraphService runs in mock mode when credentials are not configured."""
    service = GraphService()
    assert service.is_mock is True


@pytest.mark.asyncio
async def test_graph_service_mock_lookup():
    """Tests user lookup in mock mode."""
    service = GraphService()

    # Valid corporate domains should return True
    assert await service.lookup_user("riya@example.com") is True
    assert await service.lookup_user("arsh@enterprise.com") is True

    # Random domains should return False
    assert await service.lookup_user("stranger@gmail.com") is False


@pytest.mark.asyncio
async def test_graph_service_mock_reset_success():
    """Tests password reset success path in mock mode."""
    service = GraphService()
    # Resetting should complete normally with no exception
    await service.reset_password("riya@example.com", "SecurePass123!")


@pytest.mark.asyncio
async def test_graph_service_mock_reset_exceptions():
    """Tests exception handling and translation during password resets in mock mode."""
    service = GraphService()

    # Test policy violation mock triggers
    with pytest.raises(GraphAPIException) as excinfo:
        await service.reset_password("riya@example.com", "violation_password")
    assert excinfo.value.error_code == "PASSWORD_POLICY_VIOLATION"
    assert "complexity" in excinfo.value.message.lower()

    # Test account disabled mock trigger
    with pytest.raises(GraphAPIException) as excinfo:
        await service.reset_password("disabled_user@example.com", "SecurePass123!")
    assert excinfo.value.error_code == "ACCOUNT_DISABLED"

    # Test account locked mock trigger
    with pytest.raises(GraphAPIException) as excinfo:
        await service.reset_password("locked_user@example.com", "SecurePass123!")
    assert excinfo.value.error_code == "ACCOUNT_LOCKED"


@pytest.mark.asyncio
async def test_graph_service_real_credentials_token_acquisition(monkeypatch):
    """Tests token acquisition when credentials are configured."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.core.config import settings

    # Configure mock credentials
    monkeypatch.setattr(settings, "ENTRA_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "ENTRA_TENANT_ID", "test-tenant-id")
    monkeypatch.setattr(settings, "ENTRA_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(
        settings, "GRAPH_SCOPES", "https://graph.microsoft.com/.default-custom"
    )

    service = GraphService()
    assert service.is_mock is False

    # Mock Redis client get to return None (cache miss)
    async def mock_redis_get(*args, **kwargs):
        return None

    async def mock_redis_set(*args, **kwargs):
        return True

    async def mock_redis_ttl(*args, **kwargs):
        return 0

    mock_redis = MagicMock()
    mock_redis.get = mock_redis_get
    mock_redis.set = mock_redis_set
    mock_redis.ttl = mock_redis_ttl

    # We patch get_redis
    monkeypatch.setattr(
        "app.services.graph_service.get_redis", AsyncMock(return_value=mock_redis)
    )

    # Mock httpx AsyncClient post
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "REAL_ACQUIRED_TOKEN"}
    mock_response.raise_for_status = MagicMock()

    # Capture the payload sent to Entra ID
    captured_payload = {}

    async def mock_post(url, data=None, **kwargs):
        nonlocal captured_payload
        captured_payload = data
        return mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        token = await service.get_access_token()
        assert token == "REAL_ACQUIRED_TOKEN"
        # Verify the correct scopes and client credentials are used
        assert captured_payload["client_id"] == "test-client-id"
        assert captured_payload["client_secret"] == "test-client-secret"
        assert (
            captured_payload["scope"] == "https://graph.microsoft.com/.default-custom"
        )


@pytest.mark.asyncio
async def test_get_user_phone_prioritizes_business_phone(monkeypatch):
    """Tests that get_user_phone prioritizes businessPhones over mobilePhone."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.core.config import settings

    monkeypatch.setattr(settings, "ENTRA_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "ENTRA_TENANT_ID", "test-tenant-id")
    monkeypatch.setattr(settings, "ENTRA_CLIENT_SECRET", "test-client-secret")

    service = GraphService()
    monkeypatch.setattr(
        service, "get_access_token", AsyncMock(return_value="mock_token")
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "businessPhones": ["+12025550199", "+12025550188"],
        "mobilePhone": "+12025550100",
    }

    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        phone = await service.get_user_phone("testuser@enterprise.com")
        assert phone == "+12025550199"


@pytest.mark.asyncio
async def test_get_user_phone_mock_mode():
    """Tests get_user_phone returns business phone in mock mode for test users."""
    service = GraphService()
    phone = await service.get_user_phone("alex.morgan@example.com")
    assert phone == "+911800123456"

    phone_none = await service.get_user_phone("unknown@example.com")
    assert phone_none is None
