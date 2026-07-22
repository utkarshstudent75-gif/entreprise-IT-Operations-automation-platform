import time
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings
from app.core.exceptions import (
    SMSAuthenticationError,
    SMSConfigurationError,
    SMSDeliveryError,
    SMSInvalidPhoneNumberError,
    SMSRateLimitError,
    SMSTimeoutError,
)
from app.core.logging_config import logger
from app.schemas.sms import SmsRequest


def mask_phone_number(phone: str) -> str:
    """
    Masks phone numbers to protect user privacy in log output.
    Example: '+15551234567' -> '+1******4567'
    """
    if not phone:
        return "****"
    clean_phone = phone.strip()
    if len(clean_phone) <= 4:
        return "****"
    prefix = clean_phone[:2]
    suffix = clean_phone[-4:]
    masked_middle = "*" * (len(clean_phone) - 6 if len(clean_phone) > 6 else 4)
    return f"{prefix}{masked_middle}{suffix}"


class NotificationProvider(ABC):
    """
    Abstract interface for notification providers.

    Maintains strict clean architecture and dependency inversion.
    Future providers (Azure Communication Services, Twilio, AWS SNS)
    must implement this interface.
    """

    @abstractmethod
    def send_sms(self, request: SmsRequest) -> None:
        """
        Sends an SMS message using the provider.
        """
        pass

    def send_otp(self, recipient: str, otp: str) -> None:
        """
        Formats a privacy-compliant OTP notification and dispatches via send_sms.
        """
        phone_number = recipient
        if "@" in recipient and settings.SMS_TEST_RECIPIENT:
            phone_number = settings.SMS_TEST_RECIPIENT

        message = (
            f"Your password reset code is {otp}. "
            f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes."
        )
        sms_request = SmsRequest(phone_number=phone_number, message=message)
        self.send_sms(sms_request)

    @abstractmethod
    def validate_configuration(self) -> None:
        """
        Validates provider configuration at application startup.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verifies provider readiness without sending an actual message.
        """
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """
    Development notification provider that logs notifications to the console/logger.
    """

    def send_sms(self, request: SmsRequest) -> None:
        masked_phone = mask_phone_number(request.phone_number)
        if settings.DEBUG:
            logger.info("Console SMS to %s: %s", masked_phone, request.message)
        else:
            logger.info("Console SMS dispatched to %s", masked_phone)

    def validate_configuration(self) -> None:
        # Development console provider requires no secrets
        pass

    def health_check(self) -> bool:
        return True


class ThirdPartySmsNotificationProvider(NotificationProvider):
    """
    Production-ready SMS Notification Provider for third-party SMS API integration.

    Features:
    - Enforces minimal SmsRequest DTO for privacy.
    - Loads authentication and base URL dynamically from environment configuration.
    - Handles transient HTTP errors (5xx, timeouts, 429) with exponential backoff retries.
    - Does NOT retry non-transient failures (400, 401, 403).
    - Masks destination phone numbers in logs.
    - Never logs secrets, tokens, or raw credentials.
    - Fails fast on invalid configuration during startup.
    - Supports readiness health checks without sending actual SMS messages.
    """

    def __init__(
        self,
        api_key: str | None = None,
        account_sid: str | None = None,
        base_url: str | None = None,
        sender_id: str | None = None,
        timeout: float | None = None,
        retry_count: int | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.SMS_API_KEY
        if self.api_key:
            self.api_key = self.api_key.strip()

        self.account_sid = (
            account_sid if account_sid is not None else settings.SMS_ACCOUNT_SID
        )
        if self.account_sid:
            self.account_sid = self.account_sid.strip()

        self.base_url = (
            base_url if base_url is not None else settings.SMS_BASE_URL
        ).rstrip("/")
        self.sender_id = sender_id if sender_id is not None else settings.SMS_SENDER_ID
        self.timeout = timeout if timeout is not None else settings.SMS_TIMEOUT_SECONDS
        self.retry_count = (
            retry_count if retry_count is not None else settings.SMS_RETRY_COUNT
        )

    def validate_configuration(self) -> None:
        """
        Fails fast if mandatory SMS provider configuration parameters are missing or invalid.
        """
        errors = []
        if not self.api_key or not self.api_key.strip():
            errors.append("SMS_API_KEY is missing or empty.")
        if not self.account_sid or not self.account_sid.strip():
            errors.append("SMS_ACCOUNT_SID is missing or empty.")
        if not self.base_url or not (
            self.base_url.startswith("http://") or self.base_url.startswith("https://")
        ):
            errors.append("SMS_BASE_URL must be a valid HTTP/HTTPS URL.")
        if self.timeout <= 0:
            errors.append("SMS_TIMEOUT_SECONDS must be greater than 0.")

        if errors:
            error_msg = (
                f"SMS Provider configuration validation failed: {'; '.join(errors)}"
            )
            logger.error(error_msg)
            raise SMSConfigurationError(error_msg)

    def health_check(self) -> bool:
        """
        Checks provider readiness without sending a real SMS.
        """
        try:
            health_url = f"{self.base_url}/health"
            headers = self._build_headers()
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(health_url, headers=headers)
                if response.status_code < 500:
                    return True
                return False
        except Exception as e:
            logger.warning("SMS Provider health check failed: %s", str(e))
            return False

    def send_sms(self, request: SmsRequest) -> None:
        """
        Dispatches an SMS request to the third-party provider API.
        """
        if not isinstance(request, SmsRequest):
            raise SMSDeliveryError(
                "Invalid payload: must be an instance of SmsRequest DTO."
            )

        masked_phone = mask_phone_number(request.phone_number)
        endpoint = (
            self.base_url
            if self.base_url.endswith("/send") or self.base_url.endswith("/messages")
            else f"{self.base_url}/send"
        )
        payload = {
            "from": self.sender_id,
            "to": request.phone_number,
            "body": request.message,
            "message": request.message,
        }
        headers = {"Content-Type": "application/json"}
        auth = (
            (self.account_sid, self.api_key)
            if (self.account_sid and self.api_key)
            else None
        )
        if not auth and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.account_sid:
            headers["X-Account-SID"] = self.account_sid

        logger.info(
            "Attempting SMS delivery to %s via ThirdPartySmsNotificationProvider",
            masked_phone,
        )

        attempt = 0
        max_attempts = max(1, self.retry_count)

        while attempt < max_attempts:
            attempt += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        endpoint, json=payload, headers=headers, auth=auth
                    )

                # Process HTTP Status Codes
                if response.status_code in (200, 201, 202):
                    logger.info(
                        "SMS successfully dispatched to %s (attempt %d/%d)",
                        masked_phone,
                        attempt,
                        max_attempts,
                    )
                    return

                # Non-transient errors (Do NOT retry)
                if response.status_code in (401, 403):
                    logger.error(
                        "SMS provider authentication failed (HTTP %d) for recipient %s",
                        response.status_code,
                        masked_phone,
                    )
                    raise SMSAuthenticationError("SMS provider authentication failed.")

                if response.status_code == 400:
                    logger.error(
                        "SMS provider rejected request as bad request (HTTP 400) for recipient %s",
                        masked_phone,
                    )
                    raise SMSInvalidPhoneNumberError(
                        "Invalid recipient phone number or message format."
                    )

                # Transient errors (Retry candidates)
                if response.status_code == 429:
                    logger.warning(
                        "SMS provider rate limited (HTTP 429) on attempt %d/%d for %s",
                        attempt,
                        max_attempts,
                        masked_phone,
                    )
                    if attempt >= max_attempts:
                        raise SMSRateLimitError(
                            "SMS provider rate limit exceeded after maximum retries."
                        )
                elif response.status_code >= 500:
                    logger.warning(
                        "SMS provider server error (HTTP %d) on attempt %d/%d for %s",
                        response.status_code,
                        attempt,
                        max_attempts,
                        masked_phone,
                    )
                    if attempt >= max_attempts:
                        raise SMSDeliveryError(
                            f"SMS provider service unavailable (HTTP {response.status_code})."
                        )
                else:
                    raise SMSDeliveryError(
                        f"SMS provider delivery failed with HTTP status {response.status_code}."
                    )

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(
                    "SMS provider network/timeout error on attempt %d/%d for %s: %s",
                    attempt,
                    max_attempts,
                    masked_phone,
                    type(e).__name__,
                )
                if attempt >= max_attempts:
                    raise SMSTimeoutError(
                        f"SMS provider connection failed: {type(e).__name__}"
                    )

            # Exponential backoff for transient retry attempts
            if attempt < max_attempts:
                time.sleep(0.2 * (2 ** (attempt - 1)))

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.account_sid:
            headers["X-Account-SID"] = self.account_sid
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def get_notification_provider() -> NotificationProvider:
    """
    Factory function to initialize the configured NotificationProvider based on application settings.
    """
    provider_type = settings.NOTIFICATION_PROVIDER.lower()
    if provider_type in ("sms", "third_party", "thirdparty"):
        provider = ThirdPartySmsNotificationProvider()
        provider.validate_configuration()
        return provider
    return ConsoleNotificationProvider()


class NotificationService:
    """
    Service responsible for sending notifications to users.
    Delegates delivery to a configured NotificationProvider implementation.
    """

    def __init__(self, provider: NotificationProvider | None = None):
        self._provider = (
            provider if provider is not None else get_notification_provider()
        )

    def send_otp(self, email_or_phone: str, otp: str) -> None:
        """
        Sends an OTP notification to the recipient using the configured provider.
        """
        self._provider.send_otp(recipient=email_or_phone, otp=otp)

    def send_sms(self, request: SmsRequest) -> None:
        """
        Sends an SMS notification using the configured provider.
        """
        self._provider.send_sms(request)

    def is_ready(self) -> bool:
        """
        Checks readiness of the notification provider.
        """
        return self._provider.health_check()


# Default singleton instance
notification_service = NotificationService()
