from unittest.mock import patch

import pytest


# 1. Real integration connectivity tests (no mocks for DB and Redis)
@pytest.mark.asyncio
async def test_real_redis_connectivity():
    from app.core.redis import redis_manager

    redis_manager.init_redis()
    assert redis_manager.client is not None
    pong = await redis_manager.ping()
    assert pong is True


@patch("app.api.v1.health.check_sms_health")
def test_ready_endpoint_real_services(mock_sms_check, client):
    # Verify health endpoint reports Redis/DB healthy with real connections
    mock_sms_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ready"
    assert json_data["data"]["database"] == "connected"
    assert json_data["data"]["redis"] == "connected"
    assert json_data["data"]["application"] == "healthy"
    assert json_data["data"]["sms_provider"] == "connected"


# 2. Mocked unit/integration tests for testing failure states
@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
@patch("app.api.v1.health.check_sms_health")
def test_ready_endpoint_all_healthy(
    mock_sms_check, mock_redis_check, mock_db_check, client
):
    mock_db_check.return_value = True
    mock_redis_check.return_value = True
    mock_sms_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ready"
    assert json_data["data"]["database"] == "connected"
    assert json_data["data"]["redis"] == "connected"
    assert json_data["data"]["application"] == "healthy"
    assert json_data["data"]["sms_provider"] == "connected"


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
@patch("app.api.v1.health.check_sms_health")
def test_ready_endpoint_db_unhealthy(
    mock_sms_check, mock_redis_check, mock_db_check, client
):
    mock_db_check.return_value = False
    mock_redis_check.return_value = True
    mock_sms_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Database" in json_data["error"]["message"]
    assert "Redis" not in json_data["error"]["message"]


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
@patch("app.api.v1.health.check_sms_health")
def test_ready_endpoint_redis_unhealthy(
    mock_sms_check, mock_redis_check, mock_db_check, client
):
    mock_db_check.return_value = True
    mock_redis_check.return_value = False
    mock_sms_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Redis" in json_data["error"]["message"]
    assert "Database" not in json_data["error"]["message"]


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
@patch("app.api.v1.health.check_sms_health")
def test_ready_endpoint_sms_unhealthy(
    mock_sms_check, mock_redis_check, mock_db_check, client
):
    mock_db_check.return_value = True
    mock_redis_check.return_value = True
    mock_sms_check.return_value = False

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "SMS Provider" in json_data["error"]["message"]
