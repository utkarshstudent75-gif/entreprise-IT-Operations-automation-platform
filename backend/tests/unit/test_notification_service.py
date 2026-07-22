from app.schemas.sms import SmsRequest
from app.services.notification_service import (
    ConsoleNotificationProvider,
    NotificationProvider,
    NotificationService,
)


class DummyProvider(NotificationProvider):
    """
    A dummy notification provider implementation for verifying that
    NotificationService properly forwards requests to its provider.
    """

    def __init__(self):
        self.sent_sms = []

    def send_sms(self, request: SmsRequest) -> None:
        self.sent_sms.append(request)

    def validate_configuration(self) -> None:
        pass

    def health_check(self) -> bool:
        return True


def test_notification_service_delegates_to_provider():
    """
    Verify that NotificationService delegatory wrapper invokes the
    underlying NotificationProvider's send_sms method with the given parameters.
    """
    provider = DummyProvider()
    service = NotificationService(provider=provider)

    service.send_otp("+15551234567", "123456")

    assert len(provider.sent_sms) == 1
    assert provider.sent_sms[0].phone_number == "+15551234567"
    assert "123456" in provider.sent_sms[0].message
    assert "5 minutes" in provider.sent_sms[0].message


def test_console_notification_provider_debug_true(monkeypatch, caplog):
    """
    Verify that in DEBUG mode, the ConsoleNotificationProvider logs the
    SMS message alongside the masked recipient.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEBUG", True)

    provider = ConsoleNotificationProvider()
    caplog.clear()

    sms_req = SmsRequest(phone_number="+15551234567", message="Your OTP is 111222")
    provider.send_sms(sms_req)

    assert any(
        "Console SMS to +1******4567: Your OTP is 111222" in record.message
        for record in caplog.records
    )


def test_console_notification_provider_debug_false(monkeypatch, caplog):
    """
    Verify that in production (DEBUG=False) mode, the ConsoleNotificationProvider
    logs a generic message with masked recipient.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEBUG", False)

    provider = ConsoleNotificationProvider()
    caplog.clear()

    sms_req = SmsRequest(phone_number="+15551234567", message="Your OTP is 333444")
    provider.send_sms(sms_req)

    assert any(
        "Console SMS dispatched to +1******4567" in record.message
        for record in caplog.records
    )


def test_notification_service_routes_email_to_test_recipient(monkeypatch):
    """
    Verify that when recipient is an email address and settings.SMS_TEST_RECIPIENT is configured,
    the OTP is routed to the configured phone number instead of the email address.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMS_TEST_RECIPIENT", "+911800123456")

    provider = DummyProvider()
    service = NotificationService(provider=provider)

    service.send_otp("user@example.com", "987654")

    assert len(provider.sent_sms) == 1
    assert provider.sent_sms[0].phone_number == "+911800123456"
    assert "987654" in provider.sent_sms[0].message
