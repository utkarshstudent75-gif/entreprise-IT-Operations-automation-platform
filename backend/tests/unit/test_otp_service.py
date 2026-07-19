from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import (
    BaseAppException,
    ExpiredOTPException,
    InvalidOTPException,
)
from app.services.otp_service import otp_service


def test_generate_otp_success(monkeypatch):
    """
    Test that generating an OTP:
      - Uses secrets.randbelow to construct a string of settings.OTP_LENGTH.
      - Saves the OTP to the repository with settings.OTP_EXPIRY_MINUTES.
      - Returns the correct OTP.
    """
    mock_save = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.save_otp", mock_save)

    # Force length and expiry settings for testing
    monkeypatch.setattr(settings, "OTP_LENGTH", 6)
    monkeypatch.setattr(settings, "OTP_EXPIRY_MINUTES", 5)

    email = "user@example.com"
    otp = otp_service.generate_otp(email)

    assert len(otp) == 6
    assert otp.isdigit()

    # Verify repository was called to save the OTP correctly
    mock_save.assert_called_once_with(
        email=email,
        otp=otp,
        expiry_minutes=5,
    )


def test_verify_otp_success(monkeypatch):
    """
    Test that verification is successful when:
      - The OTP request is found.
      - The OTP matches.
      - The OTP is not expired.
      - The maximum verification attempts are not exceeded.

    Verifies that it deletes the OTP and returns True.
    """
    mock_record = {
        "otp": "123456",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "attempts": 0,
    }
    mock_get = MagicMock(return_value=mock_record)
    mock_delete = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)
    monkeypatch.setattr(
        "app.services.otp_service.otp_repository.delete_otp", mock_delete
    )

    result = otp_service.verify_otp("user@example.com", "123456")

    assert result is True
    # Verify the OTP gets deleted upon successful verification
    mock_delete.assert_called_once_with("user@example.com")


def test_verify_otp_no_request(monkeypatch):
    """
    Test that trying to verify an OTP when no request has been generated for
    the email raises an InvalidOTPException with status 404.
    """
    mock_get = MagicMock(return_value=None)
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)

    with pytest.raises(InvalidOTPException) as exc_info:
        otp_service.verify_otp("unknown@example.com", "123456")

    assert "No OTP request found for this email." in str(exc_info.value)
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "OTP_NOT_FOUND"


def test_verify_otp_expired(monkeypatch):
    """
    Test that verifying an OTP that has expired (now > expires_at)
    raises an ExpiredOTPException, and the expired OTP is deleted from the store.
    """
    mock_record = {
        "otp": "123456",
        "expires_at": datetime.now(UTC) - timedelta(seconds=1),
        "attempts": 0,
    }
    mock_get = MagicMock(return_value=mock_record)
    mock_delete = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)
    monkeypatch.setattr(
        "app.services.otp_service.otp_repository.delete_otp", mock_delete
    )

    with pytest.raises(ExpiredOTPException) as exc_info:
        otp_service.verify_otp("expired@example.com", "123456")

    assert "OTP has expired." in str(exc_info.value)
    # Verify the expired OTP is cleaned up
    mock_delete.assert_called_once_with("expired@example.com")


def test_verify_otp_max_attempts_exceeded_initially(monkeypatch):
    """
    Test that verification fails immediately if the number of attempts stored
    on the record already equals or exceeds the maximum allowed attempts.
    The record should be deleted and a 429 status code exception raised.
    """
    monkeypatch.setattr(settings, "OTP_MAX_ATTEMPTS", 3)
    mock_record = {
        "otp": "123456",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "attempts": 3,
    }
    mock_get = MagicMock(return_value=mock_record)
    mock_delete = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)
    monkeypatch.setattr(
        "app.services.otp_service.otp_repository.delete_otp", mock_delete
    )

    with pytest.raises(BaseAppException) as exc_info:
        otp_service.verify_otp("user@example.com", "123456")

    assert "Maximum OTP verification attempts exceeded." in str(exc_info.value)
    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "TOO_MANY_ATTEMPTS"
    mock_delete.assert_called_once_with("user@example.com")


def test_verify_otp_mismatch_increments_attempts(monkeypatch):
    """
    Test that submitting a wrong OTP increments the attempts counter by 1
    and raises an InvalidOTPException (400).
    """
    monkeypatch.setattr(settings, "OTP_MAX_ATTEMPTS", 3)
    mock_record = {
        "otp": "123456",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "attempts": 1,
    }
    mock_get = MagicMock(return_value=mock_record)
    mock_delete = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)
    monkeypatch.setattr(
        "app.services.otp_service.otp_repository.delete_otp", mock_delete
    )

    with pytest.raises(InvalidOTPException) as exc_info:
        otp_service.verify_otp("user@example.com", "000000")

    assert "Invalid OTP." in str(exc_info.value)
    assert mock_record["attempts"] == 2
    # Verify it is not deleted yet since attempts (2) < max (3)
    mock_delete.assert_not_called()


def test_verify_otp_mismatch_triggers_deletion_on_max_attempts(monkeypatch):
    """
    Test that if a wrong OTP is submitted and it brings the attempts count to the limit (max),
    the OTP is deleted from the repository, and it raises an InvalidOTPException.
    """
    monkeypatch.setattr(settings, "OTP_MAX_ATTEMPTS", 3)
    mock_record = {
        "otp": "123456",
        "expires_at": datetime.now(UTC) + timedelta(minutes=5),
        "attempts": 2,
    }
    mock_get = MagicMock(return_value=mock_record)
    mock_delete = MagicMock()
    monkeypatch.setattr("app.services.otp_service.otp_repository.get_otp", mock_get)
    monkeypatch.setattr(
        "app.services.otp_service.otp_repository.delete_otp", mock_delete
    )

    with pytest.raises(InvalidOTPException) as exc_info:
        otp_service.verify_otp("user@example.com", "000000")

    assert "Invalid OTP." in str(exc_info.value)
    assert mock_record["attempts"] == 3
    # Verify the record is deleted as it reached maximum attempts (3)
    mock_delete.assert_called_once_with("user@example.com")
