# ruff: noqa: E402
import os
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

# 1. Load env variables from .env if present
load_dotenv()

# 2. Intercept and override DATABASE_URL to use the isolated test database
db_url = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/eitoap"
)
parsed = urlparse(db_url)
path = parsed.path
if path and path != "/":
    if not path.endswith("_test"):
        new_path = f"{path}_test"
    else:
        new_path = path
else:
    new_path = "/eitoap_test"

test_db_url = urlunparse(parsed._replace(path=new_path))
os.environ["DATABASE_URL"] = test_db_url

import pytest

from app.database.otp_repository import otp_repository

# 3. Register plugins for reusable fixtures
pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.client",
]


@pytest.fixture(autouse=True)
def clear_otp_store():
    """Autouse fixture to reset internal state of OTP repository between tests."""
    otp_repository._otp_store.clear()


# Speed up password hashing in tests by using a minimum work factor (rounds=4)
from passlib.context import CryptContext

from app.services.password_reset_service import password_reset_service
from app.services.user_service import user_service

password_reset_service.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
user_service.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
