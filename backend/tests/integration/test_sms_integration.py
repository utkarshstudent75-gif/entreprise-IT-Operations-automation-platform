import os

import pytest

from app.schemas.sms import SmsRequest
from app.services.notification_service import ThirdPartySmsNotificationProvider

SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_ACCOUNT_SID = os.getenv("SMS_ACCOUNT_SID", "")
SMS_BASE_URL = os.getenv("SMS_BASE_URL", "")
RUN_LIVE_SMS_TEST = os.getenv("LIVE_SMS_TEST_ENABLED", "").lower() == "true"


# Live integration tests only execute when LIVE_SMS_TEST_ENABLED=true is explicitly set in environment
pytestmark = pytest.mark.skipif(
    not (RUN_LIVE_SMS_TEST and SMS_API_KEY and SMS_ACCOUNT_SID and SMS_BASE_URL),
    reason="Live integration test skipped: Set LIVE_SMS_TEST_ENABLED=true with active credentials to enable live API testing.",
)


def test_live_sms_provider_health_check():
    """Live integration test for SMS provider health check."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=SMS_API_KEY,
        account_sid=SMS_ACCOUNT_SID,
        base_url=SMS_BASE_URL,
    )
    assert provider.health_check() is True


def test_live_sms_provider_send():
    """Live integration test for SMS dispatch."""
    provider = ThirdPartySmsNotificationProvider(
        api_key=SMS_API_KEY,
        account_sid=SMS_ACCOUNT_SID,
        base_url=SMS_BASE_URL,
    )
    test_req = SmsRequest(
        phone_number="+15550001111",
        message="Integration test password reset code: 000000. Expires in 5 minutes.",
    )
    provider.send_sms(test_req)
