# ruff: noqa: E402
import os
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

# 1. Load env variables from .env if present
load_dotenv()

# Fallback container hostnames to localhost if executing outside Docker
if not os.path.exists("/.dockerenv"):
    if os.environ.get("REDIS_HOST") == "redis":
        os.environ["REDIS_HOST"] = "127.0.0.1"

    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        if "@redis:" in redis_url:
            redis_url = redis_url.replace("@redis:", "@127.0.0.1:")
        elif "redis://redis:" in redis_url:
            redis_url = redis_url.replace("redis://redis:", "redis://127.0.0.1:")
        os.environ["REDIS_URL"] = redis_url

    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if "@postgres:" in db_url:
            db_url = db_url.replace("@postgres:", "@127.0.0.1:")
        elif "postgresql://postgres:postgres@postgres:" in db_url:
            db_url = db_url.replace(
                "postgresql://postgres:postgres@postgres:",
                "postgresql://postgres:postgres@127.0.0.1:",
            )
        os.environ["DATABASE_URL"] = db_url

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

# 3. Register plugins for reusable fixtures
pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.client",
]


# Speed up password hashing in tests by using a minimum work factor (rounds=4)
from passlib.context import CryptContext

from app.services.password_reset_service import password_reset_service
from app.services.user_service import user_service

password_reset_service.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
user_service.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)


@pytest.fixture(autouse=True)
async def cleanup_redis_client():
    from app.core.redis import redis_manager

    try:
        await redis_manager.close()
    except Exception:
        pass
    yield
    try:
        await redis_manager.close()
    except Exception:
        pass
