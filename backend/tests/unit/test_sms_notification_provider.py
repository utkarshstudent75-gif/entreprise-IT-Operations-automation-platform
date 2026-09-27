import logging
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import (
    SMSAuthenticationError,
    SMSConfigurationError,
    SMSDeliveryError,
    SMSInvalidPhoneNumberError,
    SMSRateLimitError,
    SMSTimeoutError,
)
from app.schemas.sms import SmsRequest
from app.services.notification_service import (
    ThirdPartySmsNotificationProvider,
    mask_phone_number,
)


def test_mask_phone_number():
    """Verify phone number masking utility."""
    assert mask_phone_number("+15551234567") == "+1******4567"
    assert mask_phone_number("12345") == "12****2345"
    assert mask_phone_number("123") == "****"
    assert mask_phone_number("") == "****"


def test_provider_default_initialization_from_settings(monkeypatch):
    """
    Verify ThirdPartySmsNotificationProvider loads SMS_API_KEY, SMS_ACCOUNT_SID,
    and SMS_BASE_URL from settings when initialized without explicit arguments.
    """
    from app.core.config import settings

    monkeypatch.setattr(
        settings,
        "SMS_API_KEY",
        " $${{secrets.SMS_API_KEYY}}",
    )
    monkeypatch.setattr(
        settings,
        "SMS_ACCOUNT_SID",
        " $${{secrets.ACCOUNT_ID}}",
    )
    monkeypatch.setattr(settings, "SMS_BASE_URL", "https://od2.in/api/sms/send")

    provider = ThirdPartySmsNotificationProvider()
    assert provider.api_key == "$${{secrets.SMS_API_KEYY}}"
    assert provider.account_sid == "$${{secrets.ACCOUNT_ID}}"
    assert provider.base_url == "https://od2.in/api/sms/send"


def test_validate_configuration_success():
    """Verify validation passes with complete settings."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        timeout=5.0,
    )
    provider.validate_configuration()


def test_validate_configuration_missing_secrets():
    """Verify validation raises SMSConfigurationError when required secrets are missing."""
    provider = ThirdPartySmsNotificationProvider(
        api_key="",
        account_sid="",
        base_url="invalid-url",
        timeout=-1.0,
    )
    with pytest.raises(SMSConfigurationError) as exc_info:
        provider.validate_configuration()

    assert "SMS_API_KEY is missing" in str(exc_info.value)
    assert "SMS_ACCOUNT_SID is missing" in str(exc_info.value)


def test_send_sms_success(httpx_mock=None):
    """Verify successful SMS dispatch to third-party API using BasicAuth credentials."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        sender_id="+1234567890",
        retry_count=1,
    )
    sms_req = SmsRequest(
        phone_number="+911800123456", message="Your password reset code is 123456."
    )

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        provider.send_sms(sms_req)
        assert mock_post.call_count == 1
        args, kwargs = mock_post.call_args
        assert args == ("https://od2.in/api/sms/send",)
        assert set(kwargs["json"]) == {"from", "to", "body"}
        assert kwargs["json"]["to"] == "+911800123456"
        assert kwargs["json"]["from"] == "+1234567890"
        assert kwargs["json"]["body"] == "Your password reset code is 123456."
        assert kwargs["auth"] == (
            "$${{secrets.ACCOUNT_ID}}",
            "$${{secrets.SMS_API_KEYY}}",
        )


def test_send_sms_authentication_failure():
    """Verify 401/403 HTTP status raises SMSAuthenticationError without retrying."""
    provider = ThirdPartySmsNotificationProvider(
        api_key="invalid_sk_sms_key",
        account_sid="invalid_ACCOUNT_ID",
        base_url="https://od2.in/api/sms/send",
        retry_count=3,
    )
    sms_req = SmsRequest(phone_number="+911800123456", message="Code: 123456")

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        with pytest.raises(SMSAuthenticationError):
            provider.send_sms(sms_req)
        assert mock_post.call_count == 1  # No retries on auth failure


def test_send_sms_invalid_phone_number():
    """Verify 400 Bad Request raises SMSInvalidPhoneNumberError without retrying."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        retry_count=3,
    )
    sms_req = SmsRequest(phone_number="invalid_number", message="Code: 123456")

    mock_response = MagicMock()
    mock_response.status_code = 400

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        with pytest.raises(SMSInvalidPhoneNumberError):
            provider.send_sms(sms_req)
        assert mock_post.call_count == 1  # No retries on client error 400


def test_send_sms_transient_5xx_retry_and_fail():
    """Verify transient 5xx errors are retried up to retry_count before raising SMSDeliveryError."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        retry_count=3,
    )
    sms_req = SmsRequest(phone_number="+911800123456", message="Code: 123456")

    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch("httpx.Client.post", return_value=mock_response) as mock_post, patch(
        "time.sleep"
    ):
        with pytest.raises(SMSDeliveryError):
            provider.send_sms(sms_req)
        assert mock_post.call_count == 3


def test_send_sms_rate_limit_429_retry():
    """Verify 429 rate limit is retried up to retry_count before raising SMSRateLimitError."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        retry_count=2,
    )
    sms_req = SmsRequest(phone_number="+911800123456", message="Code: 123456")

    mock_response = MagicMock()
    mock_response.status_code = 429

    with patch("httpx.Client.post", return_value=mock_response) as mock_post, patch(
        "time.sleep"
    ):
        with pytest.raises(SMSRateLimitError):
            provider.send_sms(sms_req)
        assert mock_post.call_count == 2


def test_send_sms_network_timeout_retry():
    """Verify network timeouts are retried up to retry_count before raising SMSTimeoutError."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        retry_count=2,
    )
    sms_req = SmsRequest(phone_number="+911800123456", message="Code: 123456")

    with patch(
        "httpx.Client.post", side_effect=httpx.TimeoutException("Timeout")
    ) as mock_post, patch("time.sleep"):
        with pytest.raises(SMSTimeoutError):
            provider.send_sms(sms_req)
        assert mock_post.call_count == 2


def test_privacy_and_logging_masking(caplog):
    """Verify logs mask destination phone numbers and never log API secrets or raw tokens."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
        retry_count=1,
    )
    sms_req = SmsRequest(phone_number="+911800123456", message="Code: 987654")

    mock_response = MagicMock()
    mock_response.status_code = 200

    caplog.clear()
    with caplog.at_level(logging.INFO), patch(
        "httpx.Client.post", return_value=mock_response
    ):
        provider.send_sms(sms_req)

    log_messages = [record.message for record in caplog.records]
    # Check that masked phone number is logged
    assert any("+9*******3456" in msg for msg in log_messages)

    # Check that raw unmasked phone number is NOT logged in plain text
    assert not any("+911800123456" in msg for msg in log_messages)
    # Check that secrets are NEVER logged
    assert not any("$${{secrets.SMS_API_KEYY}}" in msg for msg in log_messages)
    assert not any("$${{secrets.ACCOUNT_ID}}" in msg for msg in log_messages)


def test_provider_health_check_success(monkeypatch):
    """Check the documented message-log endpoint without sending an SMS."""
    from app.core.config import settings

    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
    )
    monkeypatch.setattr(settings, "SMS_TEST_RECIPIENT", "+18005550199")
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.Client.get", return_value=mock_response) as mock_get:
        assert provider.health_check() is True
    mock_get.assert_called_once_with(
        "https://od2.in/api/sms/messages",
        params={"to": "+18005550199"},
        auth=("$${{secrets.ACCOUNT_ID}}", "$${{secrets.SMS_API_KEYY}}"),
    )


def test_provider_health_check_failure(monkeypatch):
    """Treat non-success responses from the documented endpoint as unhealthy."""
    from app.core.config import settings

    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
    )
    monkeypatch.setattr(settings, "SMS_TEST_RECIPIENT", "+18005550199")
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.Client.get", return_value=mock_response):
        assert provider.health_check() is False


def test_provider_health_check_network_failure(monkeypatch):
    """Return unhealthy when the provider inbox endpoint cannot be reached."""
    from app.core.config import settings

    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
    )
    monkeypatch.setattr(settings, "SMS_TEST_RECIPIENT", "+18005550199")
    with patch("httpx.Client.get", side_effect=httpx.NetworkError("Network down")):
        assert provider.health_check() is False


def test_provider_health_check_without_test_recipient_validates_configuration(
    monkeypatch,
):
    """Avoid an undocumented endpoint call when no test recipient is configured."""
    from app.core.config import settings

    provider = ThirdPartySmsNotificationProvider(
        api_key=" $${{secrets.SMS_API_KEYY}}",
        account_sid=" $${{secrets.ACCOUNT_ID}}",
        base_url="https://od2.in/api/sms/send",
    )
    monkeypatch.setattr(settings, "SMS_TEST_RECIPIENT", None)

    with patch("httpx.Client.get") as mock_get:
        assert provider.health_check() is True
    mock_get.assert_not_called()
