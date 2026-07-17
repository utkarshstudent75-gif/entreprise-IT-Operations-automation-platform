from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.services.notification_service import notification_service
from app.services.password_reset_service import (
    PasswordResetAlreadyUsedError,
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)


@pytest.fixture
def sqlite_db():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_password_reset_flow_works_end_to_end(sqlite_db, monkeypatch, caplog):
    user = User(username='ajay', email='ajaykumar@example.com', hashed_password='oldhash')
    sqlite_db.add(user)
    sqlite_db.commit()
    sqlite_db.refresh(user)

    sent_notifications = []
    monkeypatch.setattr(notification_service, 'send_otp', lambda email, otp: sent_notifications.append((email, otp)))

    caplog.set_level('INFO')
    result = password_reset_service.request_password_reset(sqlite_db, user.email)

    assert result is True
    assert sent_notifications, 'OTP notification should be sent'
    assert sent_notifications[0][0] == user.email
    assert len(sent_notifications[0][1]) == 6

    reset_request = sqlite_db.query(PasswordResetRequest).filter_by(user_id=user.id).one()
    assert reset_request.is_used is False
    assert reset_request.expires_at > datetime.utcnow()
    assert 'Password reset request created for user id' in caplog.text

    otp_code = sent_notifications[0][1]
    assert password_reset_service.verify_otp(sqlite_db, user.email, otp_code) is True

    assert password_reset_service.reset_password(sqlite_db, user.email, otp_code, 'NewPassword@123') is True

    sqlite_db.refresh(user)
    sqlite_db.refresh(reset_request)
    assert user.hashed_password != 'oldhash'
    assert reset_request.is_used is True
    assert 'Password reset completed for user id' in caplog.text

    with pytest.raises(PasswordResetAlreadyUsedError):
        password_reset_service.reset_password(sqlite_db, user.email, otp_code, 'AnotherPass@123')


def test_expired_otp_is_rejected(sqlite_db):
    user = User(username='ajay2', email='expired@example.com', hashed_password='oldhash2')
    sqlite_db.add(user)
    sqlite_db.commit()
    sqlite_db.refresh(user)

    expired_request = PasswordResetRequest(
        user_id=user.id,
        otp='000999',
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        is_used=False,
        created_at=datetime.utcnow(),
    )
    sqlite_db.add(expired_request)
    sqlite_db.commit()

    with pytest.raises(PasswordResetExpiredError):
        password_reset_service.reset_password(sqlite_db, user.email, '000999', 'NewPassword@123')


def test_unknown_email_request_returns_success(sqlite_db):
    assert password_reset_service.request_password_reset(sqlite_db, 'missing@example.com') is True


def test_verify_otp_rejects_invalid_code(sqlite_db):
    user = User(username='ajay3', email='mismatch@example.com', hashed_password='oldhash3')
    sqlite_db.add(user)
    sqlite_db.commit()
    sqlite_db.refresh(user)

    reset_request = PasswordResetRequest(
        user_id=user.id,
        otp='123456',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        is_used=False,
        created_at=datetime.utcnow(),
    )
    sqlite_db.add(reset_request)
    sqlite_db.commit()

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(sqlite_db, user.email, '000000')
