import pytest
from app.services.notification_service import (
    NotificationProvider,
    ConsoleNotificationProvider,
    NotificationService,
)


class DummyProvider(NotificationProvider):
    """
    A simple dummy provider for testing.
    """
    def __init__(self):
        self.sent = []

    def send_otp(self, email: str, otp: str) -> None:
        self.sent.append((email, otp))


def test_notification_service_delegates_to_provider():
    provider = DummyProvider()
    service = NotificationService(provider=provider)
    
    service.send_otp("user@example.com", "123456")
    
    assert len(provider.sent) == 1
    assert provider.sent[0] == ("user@example.com", "123456")


def test_console_notification_provider_debug_true(monkeypatch, caplog):
    from app.core.config import settings
    monkeypatch.setattr(settings, "DEBUG", True)
    
    provider = ConsoleNotificationProvider()
    caplog.clear()
    
    provider.send_otp("debug@example.com", "111222")
    
    assert any("OTP for debug@example.com: 111222" in record.message for record in caplog.records)


def test_console_notification_provider_debug_false(monkeypatch, caplog):
    from app.core.config import settings
    monkeypatch.setattr(settings, "DEBUG", False)
    
    provider = ConsoleNotificationProvider()
    caplog.clear()
    
    provider.send_otp("nodebug@example.com", "333444")
    
    # In non-debug mode, it should log that an OTP was generated, but NOT reveal the OTP code itself.
    assert any("OTP generated for nodebug@example.com" in record.message for record in caplog.records)
    assert not any("333444" in record.message for record in caplog.records)
