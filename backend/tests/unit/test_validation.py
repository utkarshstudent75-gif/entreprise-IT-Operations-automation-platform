import pytest
from pydantic import ValidationError

from app.schemas.password import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyOtpRequest,
)
from app.schemas.user import UserCreate


def test_user_create_validation_success():
    """
    Verify that UserCreate schema successfully instantiates with valid parameters:
      - username length >= 3 and <= 100
      - valid email
      - password length >= 8
    """
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "securepassword123",
    }
    user_create = UserCreate(**data)
    assert user_create.username == "alice"
    assert user_create.email == "alice@example.com"
    assert user_create.password == "securepassword123"


def test_user_create_validation_username_too_short():
    """
    Verify that UserCreate raises ValidationError when the username is less than 3 characters.
    """
    data = {
        "username": "jo",
        "email": "jo@example.com",
        "password": "securepassword123",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("username",)
    assert "at least 3 characters" in errors[0]["msg"]


def test_user_create_validation_username_too_long():
    """
    Verify that UserCreate raises ValidationError when the username exceeds 100 characters.
    """
    long_username = "a" * 101
    data = {
        "username": long_username,
        "email": "user@example.com",
        "password": "securepassword123",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("username",)
    assert "at most 100 characters" in errors[0]["msg"]


def test_user_create_validation_invalid_email():
    """
    Verify that UserCreate raises ValidationError when the email format is invalid.
    """
    data = {
        "username": "valid_user",
        "email": "invalid-email-format",
        "password": "securepassword123",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)

    errors = exc_info.value.errors()
    assert any(err["loc"] == ("email",) for err in errors)


def test_user_create_validation_password_too_short():
    """
    Verify that UserCreate raises ValidationError when the password is less than 8 characters.
    """
    data = {
        "username": "valid_user",
        "email": "user@example.com",
        "password": "short",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**data)

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("password",)
    assert "at least 8 characters" in errors[0]["msg"]


def test_forgot_password_request_validation():
    """
    Verify ForgotPasswordRequest:
      - Accepts a valid email address.
      - Rejects an invalid email address.
    """
    # Success case
    req = ForgotPasswordRequest(email="valid@example.com")
    assert req.email == "valid@example.com"

    # Failure case
    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="invalid_email")


def test_verify_otp_request_validation():
    """
    Verify VerifyOtpRequest:
      - Validates the email address.
      - Requires the OTP field.
    """
    # Success case
    req = VerifyOtpRequest(email="user@example.com", otp="123456")
    assert req.email == "user@example.com"
    assert req.otp == "123456"

    # Missing OTP case
    with pytest.raises(ValidationError) as exc_info:
        VerifyOtpRequest(email="user@example.com")
    assert any(err["loc"] == ("otp",) for err in exc_info.value.errors())

    # Invalid email case
    with pytest.raises(ValidationError) as exc_info:
        VerifyOtpRequest(email="bademail", otp="123456")
    assert any(err["loc"] == ("email",) for err in exc_info.value.errors())


def test_reset_password_request_validation():
    """
    Verify ResetPasswordRequest:
      - Requires a valid email.
      - Requires an OTP code.
      - Requires a new password.
    """
    # Success case
    req = ResetPasswordRequest(
        email="user@example.com", otp="123456", new_password="NewSecurePassword123!"
    )
    assert req.email == "user@example.com"
    assert req.otp == "123456"
    assert req.new_password == "NewSecurePassword123!"

    # Missing new password
    with pytest.raises(ValidationError) as exc_info:
        ResetPasswordRequest(email="user@example.com", otp="123456")
    assert any(err["loc"] == ("new_password",) for err in exc_info.value.errors())
