from datetime import datetime, timedelta

import pytest

from app.repositories.password_reset_repository import password_reset_repository
from app.repositories.user_repository import user_repository
from app.services.password_reset_service import (
    PasswordResetAlreadyUsedError,
    PasswordResetExpiredError,
    PasswordResetInvalidRequest,
    password_reset_service,
)
from app.models.user import User
from app.models.password_reset_request import PasswordResetRequest


class DummyDB:
    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def add(self, _):
        pass

    def commit(self):
        pass

    def refresh(self, _):
        pass


class DummyUser(User):
    def __init__(self, id: int, email: str):
        self.id = id
        self.email = email
        self.hashed_password = ''


class DummyResetRequest(PasswordResetRequest):
    pass


def test_request_password_reset_returns_success_for_unknown_email(monkeypatch):
    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: None)

    result = password_reset_service.request_password_reset(DummyDB(), 'missing@example.com')

    assert result is True


def test_request_password_reset_creates_request_and_sends_otp(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    created = {}

    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'create_reset_request', lambda db, user_id, otp, expires_at: created.update({'user_id': user_id, 'otp': otp, 'expires_at': expires_at}) or DummyResetRequest())
    monkeypatch.setattr('app.services.password_reset_service.notification_service.send_otp', lambda email, otp: None)

    result = password_reset_service.request_password_reset(DummyDB(), user.email)

    assert result is True
    assert created['user_id'] == user.id
    assert len(created['otp']) == 6
    assert created['expires_at'] > datetime.utcnow()


def test_verify_otp_raises_when_no_user(monkeypatch):
    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: None)

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), 'missing@example.com', '000000')


def test_verify_otp_raises_when_no_request(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'get_latest_request', lambda db, user_id: None)

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), user.email, '000000')


def test_verify_otp_raises_when_expired(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    reset_request = PasswordResetRequest(
        user_id=1,
        otp='123456',
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'get_latest_request', lambda db, user_id: reset_request)

    with pytest.raises(PasswordResetExpiredError):
        password_reset_service.verify_otp(DummyDB(), user.email, '123456')


def test_verify_otp_raises_when_mismatch(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    reset_request = PasswordResetRequest(
        user_id=1,
        otp='123456',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'get_latest_request', lambda db, user_id: reset_request)

    with pytest.raises(PasswordResetInvalidRequest):
        password_reset_service.verify_otp(DummyDB(), user.email, '000000')


def test_verify_otp_returns_true_for_matching_otp(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    reset_request = PasswordResetRequest(
        user_id=1,
        otp='123456',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'get_latest_request', lambda db, user_id: reset_request)

    assert password_reset_service.verify_otp(DummyDB(), user.email, '123456') is True

def test_reset_password_marks_request_used_and_updates_password(monkeypatch):
    user = DummyUser(id=1, email='test@example.com')
    user.hashed_password = 'oldhash'
    reset_request = PasswordResetRequest(
        user_id=1,
        otp='123456',
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    reset_request.is_used = False

    monkeypatch.setattr(user_repository, 'get_by_email', lambda db, email: user)
    monkeypatch.setattr(password_reset_repository, 'get_latest_request', lambda db, user_id: reset_request)

    assert password_reset_service.reset_password(DummyDB(), user.email, '123456', 'NewPassword@123') is True
    assert reset_request.is_used is True
    assert user.hashed_password != 'oldhash'
