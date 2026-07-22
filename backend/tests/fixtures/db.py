import os
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.base import Base


def create_test_database():
    """Ensure the isolated test database exists.

    Reads DATABASE_URL from environment, parses it, connects to the default
    'postgres' database, and runs CREATE DATABASE if it doesn't already exist.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return

    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/")

    # Connect to the default 'postgres' database to create the test database
    postgres_parsed = parsed._replace(path="/postgres")
    postgres_url = urlunparse(postgres_parsed)

    # We must use isolation_level="AUTOCOMMIT" to execute CREATE DATABASE
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        )
        if not result.scalar():
            conn.execute(text(f"CREATE DATABASE {db_name}"))
    engine.dispose()


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped database engine.

    Ensures the test database exists, creates all tables, yields the engine,
    and drops all tables on tear down.
    """
    create_test_database()

    db_url = os.environ.get("DATABASE_URL")
    engine = create_engine(db_url, pool_pre_ping=True)

    # Create all tables on test database
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after the entire test suite completes
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db(db_engine, clean_tables):
    """Function-scoped SQLAlchemy Session fixture.

    Yields an active database session and guarantees it is closed at the end of the test.
    """
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def clean_tables(db_engine):
    """Runs before database tests to clean up database state.

    Truncates all tables in PostgreSQL with CASCADE to ensure test isolation.
    """
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        session.execute(text("TRUNCATE TABLE audit_logs, users CASCADE"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
