from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.routers import password_reset
from app.core.rate_limiter import rate_limiter
from app.database.dependencies import get_db
from app.main import app
from app.services.audit_service import audit_service
from app.services.password_reset_service import password_reset_service


def test_metrics_endpoint_exposes_http_metrics_and_auth_failures(monkeypatch):
    monkeypatch.setattr(audit_service, "record_event", lambda **kwargs: None)
    with TestClient(app) as client:
        health_response = client.get("/health")
        auth_response = client.get("/api/v1/users/me")
        metrics_response = client.get("/metrics")
        metrics_alias_response = client.get("/api/v1/metrics")

    assert health_response.status_code == 200
    assert auth_response.status_code == 401
    assert metrics_response.status_code == 200
    assert metrics_alias_response.status_code == 200
    assert metrics_response.headers["content-type"].startswith("text/plain")
    assert 'http_requests_total{handler="/health",method="GET",status="200"}' in (
        metrics_response.text
    )
    assert "http_request_duration_seconds_bucket" in metrics_alias_response.text
    assert "http_request_duration_seconds_bucket" in metrics_response.text
    assert 'eitoap_authentication_failures_total{status_code="401"}' in (
        metrics_response.text
    )


def test_password_reset_metrics_use_bounded_labels_and_no_user_data(monkeypatch):
    monkeypatch.setattr(rate_limiter, "check_limit", lambda **kwargs: None)

    async def request_password_reset(db, email):
        return None

    monkeypatch.setattr(
        password_reset_service, "request_password_reset", request_password_reset
    )

    def get_db_override():
        yield None

    app.dependency_overrides[get_db] = get_db_override
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/password/forgot-password",
                json={"email": "private@example.com"},
            )
            metrics = client.get("/metrics").text
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert 'eitoap_password_reset_events_total{outcome="attempt",stage="request"}' in (
        metrics
    )
    assert 'eitoap_password_reset_events_total{outcome="success",stage="request"}' in (
        metrics
    )
    assert "private@example.com" not in metrics


def test_otp_verification_metrics_do_not_expose_otp_or_email(monkeypatch):
    async def do_nothing(*args, **kwargs):
        return None

    async def reject_otp(*args, **kwargs):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    monkeypatch.setattr(password_reset, "check_cooldown", do_nothing)
    monkeypatch.setattr(password_reset, "clear_failures", do_nothing)
    monkeypatch.setattr(password_reset, "record_failure", do_nothing)
    monkeypatch.setattr(rate_limiter, "check_limit", lambda **kwargs: None)
    monkeypatch.setattr(password_reset_service, "verify_otp", reject_otp)

    def get_db_override():
        yield None

    app.dependency_overrides[get_db] = get_db_override
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/password/verify-otp",
                json={"email": "private@example.com", "otp": "735194"},
            )
            metrics = client.get("/metrics").text
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 400
    assert 'eitoap_otp_verifications_total{outcome="attempt"}' in metrics
    assert 'eitoap_otp_verifications_total{outcome="failure"}' in metrics
    assert "private@example.com" not in metrics
    assert "735194" not in metrics
