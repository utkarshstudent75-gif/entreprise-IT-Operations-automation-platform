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
        self.sent = []

    def send_otp(self, email: str, otp: str) -> None:
        self.sent.append((email, otp))


def test_notification_service_delegates_to_provider():
    """
    Verify that NotificationService delegatory wrapper invokes the
    underlying NotificationProvider's send_otp method with the given parameters.
    """
    provider = DummyProvider()
    service = NotificationService(provider=provider)

    service.send_otp("user@example.com", "123456")

    assert len(provider.sent) == 1
    assert provider.sent[0] == ("user@example.com", "123456")


def test_console_notification_provider_debug_true(monkeypatch, caplog):
    """
    Verify that in DEBUG mode, the ConsoleNotificationProvider logs the
    actual plain-text OTP code alongside the recipient email to the application log.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEBUG", True)

    provider = ConsoleNotificationProvider()
    caplog.clear()

    provider.send_otp("debug@example.com", "111222")

    assert any(
        "OTP for debug@example.com: 111222" in record.message
        for record in caplog.records
    )


def test_console_notification_provider_debug_false(monkeypatch, caplog):
    """
    Verify that in production (DEBUG=False) mode, the ConsoleNotificationProvider
    logs a generic message that an OTP was generated for the recipient email,
    but does NOT reveal the sensitive OTP code itself.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEBUG", False)

    provider = ConsoleNotificationProvider()
    caplog.clear()

    provider.send_otp("nodebug@example.com", "333444")

    # In non-debug mode, it should log that an OTP was generated, but NOT
    # reveal the OTP code itself.
    assert any(
        "OTP generated for nodebug@example.com" in record.message
        for record in caplog.records
    )
    assert not any("333444" in record.message for record in caplog.records)
