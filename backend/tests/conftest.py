import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# 1. Load env variables from .env if present
load_dotenv()

# 2. Intercept and override DATABASE_URL to use the isolated test database
db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eitoap")
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
