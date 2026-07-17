from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert "service" in json_data["data"]
    assert "version" in json_data["data"]


def test_live_endpoint():
    response = client.get("/live")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "alive"


@patch("app.api.v1.health.check_db_health")
def test_ready_endpoint_healthy(mock_check):
    mock_check.return_value = True
    response = client.get("/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ready"
    assert json_data["data"]["database"] == "connected"


@patch("app.api.v1.health.check_db_health")
def test_ready_endpoint_unhealthy(mock_check):
    mock_check.return_value = False
    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "connection failed" in json_data["error"]["message"]


def test_prefixed_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True


def test_prefixed_live_endpoint():
    response = client.get("/api/v1/live")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True


@patch("app.api.v1.health.check_db_health")
def test_prefixed_ready_endpoint(mock_check):
    mock_check.return_value = True
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
