from datetime import UTC, datetime, timedelta
import pytest

from app.core.rate_limiter import rate_limiter
from app.models.audit_log import AuditLog
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User


def test_complete_e2e_workflow_and_validations(client, db, caplog):
    # Isolated rate limiter store for this test
    rate_limiter.storage._requests.clear()

    # Define test data
    username = "e2e_user"
    email = "e2e_user@example.com"
    password = "OldPassword@123"
    new_password = "NewPassword@123"

    # 12. Health endpoints validation
    # health_check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["status"] == "healthy"

    # live_check
    res = client.get("/live")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["status"] == "alive"

    # ready_check (verifies PostgreSQL connection)
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["status"] == "ready"
    assert res.json()["data"]["database"] == "connected"

    # 1. User Creation validation
    # Create a user via API
    res = client.post(
        "/api/v1/users",
        json={"username": username, "email": email, "password": password},
    )
    assert res.status_code == 201
    user_data = res.json()["data"]
    assert user_data["username"] == username
    assert user_data["email"] == email
    assert "id" in user_data
    user_id = user_data["id"]

    # Verify user is stored in PostgreSQL
    user_in_db = db.query(User).filter_by(id=user_id).one()
    assert user_in_db.username == username

    # 2. Password Reset Request & 10. Unknown email identical response
    # Request password reset for a valid user
    res = client.post("/api/v1/password/forgot-password", json={"email": email})
    assert res.status_code == 200
    valid_email_response = res.json()
    assert valid_email_response["success"] is True

    # Request password reset for an unknown email
    res = client.post(
        "/api/v1/password/forgot-password", json={"email": "unknown@example.com"}
    )
    assert res.status_code == 200
    unknown_email_response = res.json()
    assert unknown_email_response == valid_email_response

    # 3. Password reset request stored in PostgreSQL
    reset_req = (
        db.query(PasswordResetRequest)
        .filter_by(user_id=user_id)
        .order_by(PasswordResetRequest.created_at.desc())
        .first()
    )
    assert reset_req is not None
    assert reset_req.is_used is False
    assert len(reset_req.otp) == 6
    otp_code = reset_req.otp

    # 4. OTP verification validation
    # Verify valid OTP
    res = client.post(
        "/api/v1/password/verify-otp", json={"email": email, "otp": otp_code}
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["message"] == "OTP verified successfully."

    # 5. Password Reset & 6. Password hash updated & 7. OTP marked as used
    # Perform password reset
    res = client.post(
        "/api/v1/password/reset-password",
        json={"email": email, "otp": otp_code, "new_password": new_password},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Verify password hash updated in PostgreSQL
    db.refresh(user_in_db)
    assert user_in_db.hashed_password != password

    # Verify OTP is marked as used
    db.refresh(reset_req)
    assert reset_req.is_used is True

    # 8. Reused OTP rejected
    # Verify reused OTP rejected on verify-otp
    res = client.post(
        "/api/v1/password/verify-otp", json={"email": email, "otp": otp_code}
    )
    assert res.status_code == 400
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "OTP_ALREADY_USED"

    # Verify reused OTP rejected on reset-password
    res = client.post(
        "/api/v1/password/reset-password",
        json={
            "email": email,
            "otp": otp_code,
            "new_password": "AnotherNewPassword@123",
        },
    )
    assert res.status_code == 400
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "OTP_ALREADY_USED"

    # 9. Expired OTP rejected
    # Generate another OTP for testing expiry
    res = client.post("/api/v1/password/forgot-password", json={"email": email})
    assert res.status_code == 200
    expired_req = (
        db.query(PasswordResetRequest)
        .filter_by(user_id=user_id, is_used=False)
        .order_by(PasswordResetRequest.created_at.desc())
        .first()
    )
    assert expired_req is not None
    expired_otp = expired_req.otp

    # Manually expire it in the database
    expired_req.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    db.commit()

    # Verify expired OTP is rejected on verify-otp
    res = client.post(
        "/api/v1/password/verify-otp", json={"email": email, "otp": expired_otp}
    )
    assert res.status_code == 410
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "EXPIRED_OTP"

    # Verify expired OTP is rejected on reset-password
    res = client.post(
        "/api/v1/password/reset-password",
        json={
            "email": email,
            "otp": expired_otp,
            "new_password": "YetAnotherPassword@123",
        },
    )
    assert res.status_code == 410
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "EXPIRED_OTP"

    # 11. Audit log entries created for all major actions in PostgreSQL
    audit_logs = db.query(AuditLog).filter_by(user_id=user_id).all()
    actions = [log.action for log in audit_logs]
    statuses = [log.status for log in audit_logs]

    # Verify user_creation succeeded
    assert "user_creation" in actions
    # Verify forgot_password succeeded
    assert "forgot_password" in actions
    # Verify otp_verification succeeded
    assert "otp_verification" in actions
    # Verify password_reset succeeded
    assert "password_reset" in actions
    assert "SUCCESS" in statuses

    # Verify audit logs capture failed actions as well
    failed_audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id, AuditLog.status == "FAILED")
        .all()
    )
    assert len(failed_audit_logs) > 0
    failed_reasons = [
        log.details.get("reason") for log in failed_audit_logs if log.details
    ]
    assert "OTP already used" in failed_reasons or "OTP expired" in failed_reasons

    # 13. Structured logging validation
    # Verify response contains x-request-id header
    assert "x-request-id" in res.headers
    assert res.headers["x-request-id"] is not None

    # 14. Exception handling validation
    # Trigger validation exception (invalid email format)
    res = client.post(
        "/api/v1/password/forgot-password", json={"email": "not-an-email"}
    )
    assert res.status_code == 422
    validation_res = res.json()
    assert validation_res["success"] is False
    assert validation_res["error"]["code"] == "VALIDATION_ERROR"
    assert (
        "value is not a valid email address" in validation_res["error"]["message"]
    )

    # 15. Rate limiting validation
    # forgot-password limit is 5 requests per 10 minutes.
    # We clear the requests cache first to isolate rate limit test
    rate_limiter.storage._requests.clear()

    # Fire 5 requests (should succeed)
    for _ in range(5):
        res = client.post("/api/v1/password/forgot-password", json={"email": email})
        assert res.status_code == 200

    # 6th request should fail with 429
    res = client.post("/api/v1/password/forgot-password", json={"email": email})
    assert res.status_code == 429
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "TOO_MANY_REQUESTS"
