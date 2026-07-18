import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.dependencies import get_db

@pytest.fixture
def client(db):
    """Provides a TestClient initialized with dependency overrides for the database.
    
    Overrides the get_db dependency to yield the function-scoped test database session.
    Automatically clears overrides after the test completes.
    """
    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
