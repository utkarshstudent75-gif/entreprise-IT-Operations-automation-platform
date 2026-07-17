from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logging_config import logger


class NotificationProvider(ABC):
    """
    Interface for notification providers.
    
    Future providers like SendGrid, Twilio, or Azure Communication Services
    should subclass this and implement the methods.
    """

    @abstractmethod
    def send_otp(self, email: str, otp: str) -> None:
        """
        Sends an OTP (One-Time Password) to the specified email/recipient.
        """
        pass


class ConsoleNotificationProvider(NotificationProvider):
    """
    Notification provider that logs OTPs to the console/logger.
    """

    def send_otp(self, email: str, otp: str) -> None:
        if settings.DEBUG:
            logger.info("OTP for %s: %s", email, otp)
        else:
            logger.info("OTP generated for %s", email)


class NotificationService:
    """
    Service responsible for sending notifications to users.
    It delegates actual delivery to a configured NotificationProvider.
    """

    def __init__(self, provider: NotificationProvider):
        self._provider = provider

    def send_otp(self, email: str, otp: str) -> None:
        self._provider.send_otp(email, otp)


# Default instance initialized with ConsoleNotificationProvider for backward compatibility.
notification_service = NotificationService(ConsoleNotificationProvider())