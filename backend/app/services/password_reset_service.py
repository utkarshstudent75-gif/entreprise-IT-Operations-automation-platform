import secrets

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.context import logging_context, user_id
from app.core.exceptions import (
    ExpiredOTPException,
    InvalidOTPException,
    OTPAlreadyUsedException,
    PasswordResetException,
)
from app.core.logging_config import logger
from app.repositories.user_repository import user_repository
from app.services.audit_service import audit_service
from app.services.graph_service import graph_service
from app.services.notification_service import notification_service
from app.services.redis_service import redis_service

INVALID_EMAIL_OR_OTP = "Invalid email or OTP."
OTP_EXPIRED = "OTP has expired."
OTP_ALREADY_USED_MSG = "OTP has already been used."


class PasswordResetError(PasswordResetException):
    """Base exception for password reset business rules."""

    def __init__(self, message: str = "Password reset error."):
        super().__init__(message)


class PasswordResetInvalidRequest(PasswordResetError, InvalidOTPException):
    """Raised when the submitted OTP or email cannot be validated."""

    def __init__(self, message: str = INVALID_EMAIL_OR_OTP):
        super().__init__(message)
        self.error_code = "INVALID_OTP"
        self.status_code = 400


class PasswordResetExpiredError(PasswordResetError, ExpiredOTPException):
    """Raised when the OTP has expired."""

    def __init__(self, message: str = OTP_EXPIRED):
        super().__init__(message)
        self.error_code = "EXPIRED_OTP"
        self.status_code = 410


class PasswordResetAlreadyUsedError(PasswordResetError, OTPAlreadyUsedException):
    """Raised when the OTP has already been consumed."""

    def __init__(self, message: str = OTP_ALREADY_USED_MSG):
        super().__init__(message)
        self.error_code = "OTP_ALREADY_USED"
        self.status_code = 400


class PasswordResetService:
    """Encapsulates password reset business logic separate from repository code."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def validate_password_strength(self, password: str) -> None:
        """
        Validates password complexity against system configuration and weak blacklists.
        Raises GraphAPIException if complexity rules are not met.
        """
        import re

        from app.services.graph_service import GraphAPIException

        # 1. Length check
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise GraphAPIException(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long.",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )

        # 2. Case checks
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            raise GraphAPIException(
                "Password must contain at least one uppercase letter (A-Z).",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            raise GraphAPIException(
                "Password must contain at least one lowercase letter (a-z).",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )

        # 3. Numeric checks
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
            raise GraphAPIException(
                "Password must contain at least one digit (0-9).",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )

        # 4. Special character checks
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(
            r"[^A-Za-z0-9]", password
        ):
            raise GraphAPIException(
                "Password must contain at least one special character (e.g. !@#$%^&*).",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )

        # 5. Blacklisted weak passwords check
        weak_blacklist = ["password", "12345678", "admin123", "password123", "qwerty"]
        if password.lower() in weak_blacklist:
            raise GraphAPIException(
                "The password meets standard rules but is too common or weak.",
                status_code=400,
                error_code="PASSWORD_POLICY_VIOLATION",
            )

    async def request_password_reset(self, db: Session, email: str) -> None:
        """Create a reset request and send the OTP.

        If the user does not exist in Microsoft Entra ID, complete the call successfully
        anyway to prevent user enumeration. This avoids leaking whether an email is registered.
        """
        with logging_context(act="password_reset_requested"):
            # Check user presence in Microsoft Entra ID
            user_exists = await graph_service.lookup_user(email)

            # Map user ID from local database if available for log correlation
            local_user = user_repository.get_by_email(db, email)
            if local_user:
                user_id.set(local_user.id)

            if not user_exists:
                logger.info("Password reset requested for an unregistered account.")
                audit_service.record_event(
                    action="forgot_password",
                    status="FAILED",
                    details={"email": email, "reason": "Unknown email"},
                )
                return

            otp = self._generate_otp()

            try:
                await redis_service.store_otp(
                    email=email,
                    otp=otp,
                    expires_in_seconds=settings.OTP_EXPIRY_MINUTES * 60,
                )
            except Exception as e:
                logger.error(
                    "Failed to create password reset request (%s).",
                    type(e).__name__,
                )
                audit_service.record_event(
                    action="forgot_password",
                    status="FAILED",
                    user_id=local_user.id if local_user else None,
                    details={"email": email, "reason": str(e)},
                )
                raise

            # Resolve user phone from Microsoft Graph
            phone_number = await graph_service.get_user_phone(email)
            recipient = phone_number if phone_number else email

            # Send the OTP using notification_service
            notification_service.send_otp(recipient, otp)

            logger.info("Password reset request created.")
            audit_service.record_event(
                action="forgot_password",
                status="SUCCESS",
                user_id=local_user.id if local_user else None,
                details={"email": email},
            )

    async def verify_otp(self, db: Session, email: str, otp: str) -> bool:
        """Verify a submitted OTP without consuming it."""
        with logging_context(act="otp_verification"):
            user_exists = await graph_service.lookup_user(email)
            local_user = user_repository.get_by_email(db, email)
            if local_user:
                user_id.set(local_user.id)

            if not user_exists:
                logger.warning("Password reset OTP verification failed.")
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    details={
                        "email": email,
                        "reason": INVALID_EMAIL_OR_OTP.rstrip("."),
                    },
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            try:
                await redis_service.verify_otp(
                    email=email,
                    otp=otp,
                    consume=False,
                    max_attempts=settings.OTP_MAX_ATTEMPTS,
                    expires_in_seconds=settings.OTP_EXPIRY_MINUTES * 60,
                )
            except Exception as e:
                logger.warning("OTP verification failed (%s).", type(e).__name__)
                from app.core.exceptions import (
                    ExpiredOTPException,
                    OTPAlreadyUsedException,
                )

                if isinstance(e, ExpiredOTPException):
                    reason = "OTP expired"
                    audit_service.record_event(
                        action="otp_verification",
                        status="FAILED",
                        user_id=local_user.id if local_user else None,
                        details={"email": email, "reason": reason},
                    )
                    raise PasswordResetExpiredError(OTP_EXPIRED)
                elif isinstance(e, OTPAlreadyUsedException):
                    reason = "OTP already used"
                    audit_service.record_event(
                        action="otp_verification",
                        status="FAILED",
                        user_id=local_user.id if local_user else None,
                        details={"email": email, "reason": reason},
                    )
                    raise PasswordResetAlreadyUsedError(OTP_ALREADY_USED_MSG)

                reason = "OTP mismatch"
                audit_service.record_event(
                    action="otp_verification",
                    status="FAILED",
                    user_id=local_user.id if local_user else None,
                    details={"email": email, "reason": reason},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            logger.info("Password reset OTP verified.")
            audit_service.record_event(
                action="otp_verification",
                status="SUCCESS",
                user_id=local_user.id if local_user else None,
                details={"email": email},
            )
            return True

    async def reset_password(
        self,
        db: Session,
        email: str,
        otp: str,
        new_password: str,
        confirm_password: str | None = None,
    ) -> bool:
        """Reset a user's password in Entra ID via Microsoft Graph after validating OTP."""
        if confirm_password is not None and new_password != confirm_password:
            from app.services.graph_service import GraphAPIException

            raise GraphAPIException(
                "Passwords do not match.",
                status_code=400,
                error_code="PASSWORD_MISMATCH",
            )

        with logging_context(act="password_reset_completed"):
            user_exists = await graph_service.lookup_user(email)
            local_user = user_repository.get_by_email(db, email)
            if local_user:
                user_id.set(local_user.id)

            if not user_exists:
                logger.warning("Password reset failed for an unregistered account.")
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    details={
                        "email": email,
                        "reason": INVALID_EMAIL_OR_OTP.rstrip("."),
                    },
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            # 1. Verify OTP first (consumes on success)
            try:
                await redis_service.verify_otp(
                    email=email,
                    otp=otp,
                    consume=True,
                    max_attempts=settings.OTP_MAX_ATTEMPTS,
                    expires_in_seconds=settings.OTP_EXPIRY_MINUTES * 60,
                )
            except Exception as e:
                logger.warning(
                    "OTP verification for password reset failed (%s).",
                    type(e).__name__,
                )
                from app.core.exceptions import (
                    ExpiredOTPException,
                    OTPAlreadyUsedException,
                )

                if isinstance(e, ExpiredOTPException):
                    reason = "OTP expired"
                    audit_service.record_event(
                        action="password_reset",
                        status="FAILED",
                        user_id=local_user.id if local_user else None,
                        details={"email": email, "reason": reason},
                    )
                    raise PasswordResetExpiredError(OTP_EXPIRED)
                elif isinstance(e, OTPAlreadyUsedException):
                    reason = "OTP already used"
                    audit_service.record_event(
                        action="password_reset",
                        status="FAILED",
                        user_id=local_user.id if local_user else None,
                        details={"email": email, "reason": reason},
                    )
                    raise PasswordResetAlreadyUsedError(OTP_ALREADY_USED_MSG)

                reason = "OTP mismatch"
                audit_service.record_event(
                    action="password_reset",
                    status="FAILED",
                    user_id=local_user.id if local_user else None,
                    details={"email": email, "reason": reason},
                )
                raise PasswordResetInvalidRequest(INVALID_EMAIL_OR_OTP)

            # 2. Validate password strength against Pydantic policy rules
            self.validate_password_strength(new_password)

            # 3. Call Microsoft Graph client to reset the password
            try:
                audit_service.record_event(
                    action="graph_password_reset_initiated",
                    status="SUCCESS",
                    user_id=local_user.id if local_user else None,
                    details={"email": email},
                )

                await graph_service.reset_password(email, new_password)

                audit_service.record_event(
                    action="graph_password_reset_successful",
                    status="SUCCESS",
                    user_id=local_user.id if local_user else None,
                    details={"email": email},
                )
            except Exception as e:
                from app.services.graph_service import GraphAPIException

                reason = (
                    str(e)
                    if isinstance(e, GraphAPIException)
                    else "Graph integration error"
                )

                audit_service.record_event(
                    action="graph_password_reset_failed",
                    status="FAILED",
                    user_id=local_user.id if local_user else None,
                    details={"email": email, "reason": reason},
                )
                raise

            logger.info("Password reset completed successfully via Graph.")
            audit_service.record_event(
                action="password_reset",
                status="SUCCESS",
                user_id=local_user.id if local_user else None,
                details={"email": email},
            )
            return True

    def _generate_otp(self) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(6))


password_reset_service = PasswordResetService()
