import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.otp_repository import otp_repository


@pytest.fixture(autouse=True)
def clear_otp_store():
    otp_repository._otp_store.clear()


@pytest.fixture(autouse=True)
def mock_audit_session_local(monkeypatch):
    """
    Global autouse fixture to patch SessionLocal in audit_service for all tests.
    This prevents tests from hanging by attempting to connect to PostgreSQL.
    """
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr("app.services.audit_service.SessionLocal", TestSessionLocal)
