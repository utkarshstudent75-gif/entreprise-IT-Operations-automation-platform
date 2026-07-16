import pytest

from app.database.otp_repository import otp_repository


@pytest.fixture(autouse=True)
def clear_otp_store():
    otp_repository._otp_store.clear()