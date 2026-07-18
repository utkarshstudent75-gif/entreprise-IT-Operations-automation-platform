from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limiter import rate_limiter
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter_store():
    # Clear the in-memory store before each test to keep tests isolated
    rate_limiter.storage._requests.clear()


@patch("time.time")
def test_forgot_password_rate_limiting(mock_time):
    mock_time.return_value = 1000.0

    # Mock password reset service to prevent DB connections/raising errors
    with patch("app.api.v1.password.password_reset_service.request_password_reset"):
        # First 5 requests should succeed
        for _ in range(5):
            response = client.post(
                "/api/v1/password/forgot-password",
                json={"email": "test@example.com"},
            )
            assert response.status_code == 200

        # 6th request should fail with 429
        response = client.post(
            "/api/v1/password/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 429
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "TOO_MANY_REQUESTS"

        # Request for a different email should still succeed
        response = client.post(
            "/api/v1/password/forgot-password",
            json={"email": "other@example.com"},
        )
        assert response.status_code == 200

        # Advance time by 10 minutes (600 seconds) + 1 second
        mock_time.return_value = 1601.0

        # Now it should be allowed again
        response = client.post(
            "/api/v1/password/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200


@patch("time.time")
def test_verify_otp_rate_limiting(mock_time):
    mock_time.return_value = 1000.0

    with patch("app.api.v1.password.password_reset_service.verify_otp"):
        # First 10 requests should succeed
        for _ in range(10):
            response = client.post(
                "/api/v1/password/verify-otp",
                json={"email": "test@example.com", "otp": "123456"},
            )
            assert response.status_code == 200

        # 11th request should fail with 429
        response = client.post(
            "/api/v1/password/verify-otp",
            json={"email": "test@example.com", "otp": "123456"},
        )
        assert response.status_code == 429
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "TOO_MANY_REQUESTS"

        # Different email succeeds
        response = client.post(
            "/api/v1/password/verify-otp",
            json={"email": "other@example.com", "otp": "123456"},
        )
        assert response.status_code == 200

        # Advance time by 601 seconds
        mock_time.return_value = 1601.0

        # Succeeds again
        response = client.post(
            "/api/v1/password/verify-otp",
            json={"email": "test@example.com", "otp": "123456"},
        )
        assert response.status_code == 200
