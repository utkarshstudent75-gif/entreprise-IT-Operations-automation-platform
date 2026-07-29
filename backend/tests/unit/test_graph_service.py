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
