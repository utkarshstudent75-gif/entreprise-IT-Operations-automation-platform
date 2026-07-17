from app.schemas.user import UserCreate
from app.services.user_service import user_service
from app.core.exceptions import DuplicateUserException
from sqlalchemy.orm import Session


class DummyUser:
    def __init__(self, id: int, username: str, email: str):
        self.id = id
        self.username = username
        self.email = email


class DummyDB(Session):
    pass


def test_create_user_returns_user_response(monkeypatch):
    request = UserCreate(username='utkarsh', email='utkarsh@example.com', password='Password@123')
    
    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_username',
        lambda db, username: None,
    )
    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_email',
        lambda db, email: None,
    )
    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.create_user',
        lambda db, username, email, hashed_password: DummyUser(id=1, username=username, email=email),
    )

    result = user_service.create_user(DummyDB(), request)

    assert result.id == 1
    assert result.username == 'utkarsh'
    assert result.email == 'utkarsh@example.com'


def test_create_user_conflict_on_existing_username(monkeypatch):
    request = UserCreate(username='utkarsh', email='utkarsh@example.com', password='Password@123')

    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_username',
        lambda db, username: DummyUser(id=1, username=username, email='existing@example.com'),
    )
    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_email',
        lambda db, email: None,
    )

    try:
        user_service.create_user(DummyDB(), request)
        assert False, 'Expected DuplicateUserException'
    except DuplicateUserException as exc:
        assert exc.status_code == 409
        assert 'Username already exists' in str(exc.detail)


def test_create_user_conflict_on_existing_email(monkeypatch):
    request = UserCreate(username='newuser', email='utkarsh@example.com', password='Password@123')

    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_username',
        lambda db, username: None,
    )
    monkeypatch.setattr(
        'app.repositories.user_repository.user_repository.get_by_email',
        lambda db, email: DummyUser(id=1, username='existinguser', email=email),
    )

    try:
        user_service.create_user(DummyDB(), request)
        assert False, 'Expected DuplicateUserException'
    except DuplicateUserException as exc:
        assert exc.status_code == 409
        assert 'Email already exists' in str(exc.detail)

