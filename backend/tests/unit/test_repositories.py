from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.sql.elements import BinaryExpression

from app.models.audit_log import AuditLog
from app.models.password_reset_request import PasswordResetRequest
from app.models.user import User
from app.repositories.audit_repository import audit_repository
from app.repositories.password_reset_repository import password_reset_repository
from app.repositories.user_repository import user_repository


# ==============================================================================
# USER REPOSITORY TESTS
# ==============================================================================

def test_user_repo_get_by_username():
    """
    Test that user_repository.get_by_username queries the database correctly
    using the session query and filter methods, returning the correct User or None.
    """
    mock_db = MagicMock()
    mock_user = User(id=1, username="testuser", email="test@example.com")
    
    # Mock chain: db.query().filter().one_or_none()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.one_or_none.return_value = mock_user

    result = user_repository.get_by_username(mock_db, "testuser")

    # Assertions
    mock_db.query.assert_called_once_with(User)
    mock_query.filter.assert_called_once()
    
    # Check that filter expression references username column
    expr = mock_query.filter.call_args[0][0]
    assert isinstance(expr, BinaryExpression)
    assert str(expr.left) == "users.username"
    assert expr.right.value == "testuser"
    
    assert result == mock_user


def test_user_repo_get_by_email():
    """
    Test that user_repository.get_by_email queries by the email address.
    """
    mock_db = MagicMock()
    mock_user = User(id=1, username="testuser", email="test@example.com")
    
    # Mock chain
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.one_or_none.return_value = mock_user

    result = user_repository.get_by_email(mock_db, "test@example.com")

    # Assertions
    mock_db.query.assert_called_once_with(User)
    mock_query.filter.assert_called_once()
    expr = mock_query.filter.call_args[0][0]
    assert isinstance(expr, BinaryExpression)
    assert str(expr.left) == "users.email"
    assert expr.right.value == "test@example.com"
    
    assert result == mock_user


def test_user_repo_get_by_id():
    """
    Test that user_repository.get_by_id queries using the user's integer ID.
    """
    mock_db = MagicMock()
    mock_user = User(id=42, username="testuser", email="test@example.com")
    
    # Mock chain
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.one_or_none.return_value = mock_user

    result = user_repository.get_by_id(mock_db, 42)

    # Assertions
    mock_db.query.assert_called_once_with(User)
    mock_query.filter.assert_called_once()
    expr = mock_query.filter.call_args[0][0]
    assert isinstance(expr, BinaryExpression)
    assert str(expr.left) == "users.id"
    assert expr.right.value == 42
    
    assert result == mock_user


def test_user_repo_create_user():
    """
    Test that user_repository.create_user instantiates a User object,
    calls db.add(), db.commit(), and db.refresh(), returning the persisted User.
    """
    mock_db = MagicMock()

    result = user_repository.create_user(
        db=mock_db,
        username="newuser",
        email="new@example.com",
        hashed_password="securehashpassword",
    )

    # Verify database session calls
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Verify fields of the added User instance
    added_user = mock_db.add.call_args[0][0]
    assert isinstance(added_user, User)
    assert added_user.username == "newuser"
    assert added_user.email == "new@example.com"
    assert added_user.hashed_password == "securehashpassword"
    assert result == added_user


# ==============================================================================
# AUDIT REPOSITORY TESTS
# ==============================================================================

def test_audit_repo_create_entry():
    """
    Test that audit_repository.create_entry persists an AuditLog with the passed parameters.
    """
    mock_db = MagicMock()
    details = {"info": "some_details"}
    timestamp = datetime(2026, 1, 1)

    result = audit_repository.create_entry(
        db=mock_db,
        action="login_attempt",
        status="SUCCESS",
        user_id=10,
        ip_address="127.0.0.1",
        user_agent="Firefox",
        request_id="req-123",
        details=details,
        timestamp=timestamp,
    )

    # Verify session interactions
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Verify constructed AuditLog values
    added_log = mock_db.add.call_args[0][0]
    assert isinstance(added_log, AuditLog)
    assert added_log.action == "login_attempt"
    assert added_log.status == "SUCCESS"
    assert added_log.user_id == 10
    assert added_log.ip_address == "127.0.0.1"
    assert added_log.user_agent == "Firefox"
    assert added_log.request_id == "req-123"
    assert added_log.details == details
    assert added_log.timestamp == timestamp
    assert result == added_log


def test_audit_repo_get_by_id():
    """
    Test that audit_repository.get_by_id executes a SELECT statement matching the ID.
    """
    mock_db = MagicMock()
    mock_log = AuditLog(id=99)
    
    # Mock chain: db.execute().scalar_one_or_none()
    mock_execute_result = mock_db.execute.return_value
    mock_execute_result.scalar_one_or_none.return_value = mock_log

    result = audit_repository.get_by_id(mock_db, 99)

    # Verify query compilation and execution
    mock_db.execute.assert_called_once()
    executed_statement = mock_db.execute.call_args[0][0]
    assert str(executed_statement).startswith("SELECT")
    assert "WHERE audit_logs.id = :id" in str(executed_statement)
    
    assert result == mock_log


def test_audit_repo_get_all_no_filters():
    """
    Test that audit_repository.get_all executes a basic query with offsets and limits
    when no filters are provided.
    """
    mock_db = MagicMock()
    mock_execute_result = mock_db.execute.return_value
    mock_execute_result.scalars.return_value.all.return_value = []

    result = audit_repository.get_all(mock_db, skip=10, limit=20)

    mock_db.execute.assert_called_once()
    statement = str(mock_db.execute.call_args[0][0])
    
    assert "SELECT" in statement
    assert "LIMIT :param_1 OFFSET :param_2" in statement
    assert result == []


def test_audit_repo_get_all_with_filters():
    """
    Test that audit_repository.get_all correctly appends filtering criteria
    to the generated SELECT statement.
    """
    mock_db = MagicMock()
    mock_execute_result = mock_db.execute.return_value
    mock_execute_result.scalars.return_value.all.return_value = []

    start_date = datetime(2026, 7, 1)
    end_date = datetime(2026, 7, 10)

    result = audit_repository.get_all(
        mock_db,
        user_id=1,
        action="password_reset",
        status="FAILED",
        start_date=start_date,
        end_date=end_date,
    )

    mock_db.execute.assert_called_once()
    statement = str(mock_db.execute.call_args[0][0])
    
    # Verify that all filters are applied in SQL WHERE clause
    assert "WHERE audit_logs.user_id = :user_id" in statement
    assert "audit_logs.action = :action" in statement
    assert "audit_logs.status = :status" in statement
    assert "audit_logs.timestamp >= :timestamp_1" in statement
    assert "audit_logs.timestamp <= :timestamp_2" in statement


# ==============================================================================
# PASSWORD RESET REPOSITORY TESTS
# ==============================================================================

def test_pw_reset_repo_create_reset_request():
    """
    Test that password_reset_repository.create_reset_request persists a PasswordResetRequest
    with the correct foreign key, otp, and expires_at fields.
    """
    mock_db = MagicMock()
    expiry = datetime(2026, 7, 18, 12, 0, 0)

    result = password_reset_repository.create_reset_request(
        db=mock_db,
        user_id=5,
        otp="987654",
        expires_at=expiry,
    )

    # Verify session interactions
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Verify request instance
    added_request = mock_db.add.call_args[0][0]
    assert isinstance(added_request, PasswordResetRequest)
    assert added_request.user_id == 5
    assert added_request.otp == "987654"
    assert added_request.expires_at == expiry
    assert result == added_request


def test_pw_reset_repo_get_latest_request():
    """
    Test that get_latest_request fetches the newest request for the given user,
    ordered by creation timestamp descending.
    """
    mock_db = MagicMock()
    mock_req = PasswordResetRequest(id=1, user_id=5)
    mock_execute_result = mock_db.execute.return_value
    mock_execute_result.scalar_one_or_none.return_value = mock_req

    result = password_reset_repository.get_latest_request(mock_db, 5)

    mock_db.execute.assert_called_once()
    statement = str(mock_db.execute.call_args[0][0])
    
    assert "WHERE password_reset_requests.user_id = :user_id" in statement
    assert "ORDER BY password_reset_requests.created_at DESC" in statement
    assert "LIMIT :param_1" in statement
    assert result == mock_req


def test_pw_reset_repo_get_latest_valid_request():
    """
    Test that get_latest_valid_request fetches only unused (is_used is False) requests
    for the given user.
    """
    mock_db = MagicMock()
    mock_req = PasswordResetRequest(id=2, user_id=5, is_used=False)
    mock_execute_result = mock_db.execute.return_value
    mock_execute_result.scalar_one_or_none.return_value = mock_req

    result = password_reset_repository.get_latest_valid_request(mock_db, 5)

    mock_db.execute.assert_called_once()
    statement = str(mock_db.execute.call_args[0][0])
    
    assert "WHERE password_reset_requests.user_id = :user_id" in statement
    assert "password_reset_requests.is_used IS false" in statement
    assert result == mock_req


def test_pw_reset_repo_mark_used():
    """
    Test that mark_used sets is_used=True and commits the update to database.
    """
    mock_db = MagicMock()
    req = PasswordResetRequest(id=3, is_used=False)

    result = password_reset_repository.mark_used(mock_db, req)

    assert req.is_used is True
    mock_db.add.assert_called_once_with(req)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(req)
    assert result == req


def test_pw_reset_repo_delete_expired_requests():
    """
    Test that delete_expired_requests executes a DELETE query to purge expired reset requests.
    """
    mock_db = MagicMock()
    password_reset_repository.delete_expired_requests(mock_db)

    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

    statement = str(mock_db.execute.call_args[0][0])
    assert "DELETE FROM password_reset_requests" in statement
    assert "WHERE password_reset_requests.expires_at <" in statement
