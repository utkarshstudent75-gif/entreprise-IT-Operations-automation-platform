from fastapi import status


class BaseAppException(Exception):
    """Base exception for all application-specific errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.detail = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class UserNotFoundException(BaseAppException):
    """Raised when a requested user is not found."""

    status_code: int = status.HTTP_404_NOT_FOUND
    error_code: str = "USER_NOT_FOUND"

    def __init__(self, message: str = "User not found."):
        super().__init__(message)


class InvalidOTPException(BaseAppException):
    """Raised when the OTP is invalid or has failed validation."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "INVALID_OTP"

    def __init__(
        self,
        message: str = "Invalid OTP.",
        status_code: int | None = None,
        error_code: str | None = None,
    ):
        super().__init__(message, status_code=status_code, error_code=error_code)


class ExpiredOTPException(BaseAppException):
    """Raised when the OTP has expired."""

    status_code: int = status.HTTP_410_GONE
    error_code: str = "EXPIRED_OTP"

    def __init__(self, message: str = "OTP has expired."):
        super().__init__(message)


class OTPAlreadyUsedException(BaseAppException):
    """Raised when the OTP has already been consumed."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "OTP_ALREADY_USED"

    def __init__(self, message: str = "OTP has already been used."):
        super().__init__(message)


class DuplicateUserException(BaseAppException):
    """Raised when a user with the same username or email already exists."""

    status_code: int = status.HTTP_409_CONFLICT
    error_code: str = "DUPLICATE_USER"

    def __init__(self, message: str = "Username or email already exists."):
        super().__init__(message)


class PasswordResetException(BaseAppException):
    """Raised when there is an issue during the password reset process."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "PASSWORD_RESET_ERROR"

    def __init__(self, message: str = "Password reset error."):
        super().__init__(message)


class RateLimitExceededException(BaseAppException):
    """Raised when rate limits are exceeded."""

    status_code: int = status.HTTP_429_TOO_MANY_REQUESTS
    error_code: str = "TOO_MANY_REQUESTS"

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message)
