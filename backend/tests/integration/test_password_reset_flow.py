from datetime import UTC, datetime, timedelta

import pytest

from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.password_reset_service import (
    PasswordResetAlreadyUsedError,
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)


def test_password_reset_flow_works_end_to_end(db, monkeypatch, caplog):
    user = User(
        username="ajay", email="ajaykumar@example.com", hashed_password="oldhash"  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    sent_notifications = []
    monkeypatch.setattr(
        notification_service,
        "send_otp",
        lambda email, otp: sent_notifications.append((email, otp)),
    )

    caplog.set_level("INFO")
    result = password_reset_service.request_password_reset(db, user.email)

    assert result is None
    assert sent_notifications, "OTP notification should be sent"
    assert sent_notifications[0][0] == user.email
    assert len(sent_notifications[0][1]) == 6

    reset_request = db.query(PasswordResetRequest).filter_by(user_id=user.id).one()
    assert reset_request.is_used is False
    assert reset_request.expires_at > datetime.now(UTC).replace(tzinfo=None)
    assert "Password reset request created for user id" in caplog.text

    otp_code = sent_notifications[0][1]
    assert password_reset_service.verify_otp(db, user.email, otp_code) is True

    assert (
        password_reset_service.reset_password(
            db, user.email, otp_code, "NewPassword@123"
        )
        is True
    )

    db.refresh(user)
    db.refresh(reset_request)
    assert user.hashed_password != "oldhash"
    assert reset_request.is_used is True
    assert "Password reset completed for user id" in caplog.text

    with pytest.raises(PasswordResetAlreadyUsedError):
        password_reset_service.reset_password(
            db, user.email, otp_code, "AnotherPass@123"
        )


def test_expired_otp_is_rejected(db):
    user = User(
        username="ajay2", email="expired@example.com", hashed_password="oldhash2"  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    expired_request = PasswordResetRequest(
        user_id=user.id,
        otp="000999",
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
        is_used=False,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(expired_request)
    db.commit()

    with pytest.raises(PasswordResetExpiredError):
        password_reset_service.reset_password(
            db, user.email, "000999", "NewPassword@123"
        )


def test_unknown_email_request_returns_success(db):
    assert (
        password_reset_service.request_password_reset(db, "missing@example.com") is None
    )


def test_verify_otp_rejects_invalid_code(db):
    user = User(
        username="ajay3", email="mismatch@example.com", hashed_password="oldhash3"  # NOSONAR
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    reset_request = PasswordResetRequest(
        user_id=user.id,
        otp="123456",
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=5),
        is_used=False,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(reset_request)
    db.commit()

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(db, user.email, "000000")
