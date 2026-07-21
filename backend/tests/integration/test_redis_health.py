from unittest.mock import patch


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
def test_ready_endpoint_both_healthy(mock_redis_check, mock_db_check, client):
    mock_db_check.return_value = True
    mock_redis_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ready"
    assert json_data["data"]["database"] == "connected"
    assert json_data["data"]["redis"] == "connected"


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
def test_ready_endpoint_db_unhealthy(mock_redis_check, mock_db_check, client):
    mock_db_check.return_value = False
    mock_redis_check.return_value = True

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Database" in json_data["error"]["message"]
    assert "Redis" not in json_data["error"]["message"]


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
def test_ready_endpoint_redis_unhealthy(mock_redis_check, mock_db_check, client):
    mock_db_check.return_value = True
    mock_redis_check.return_value = False

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Redis" in json_data["error"]["message"]
    assert "Database" not in json_data["error"]["message"]


@patch("app.api.v1.health.check_db_health")
@patch("app.api.v1.health.check_redis_health_async")
def test_ready_endpoint_both_unhealthy(mock_redis_check, mock_db_check, client):
    mock_db_check.return_value = False
    mock_redis_check.return_value = False

    response = client.get("/ready")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Database" in json_data["error"]["message"]
    assert "Redis" in json_data["error"]["message"]
