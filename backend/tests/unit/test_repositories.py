from datetime import datetime
from unittest.mock import MagicMock

from sqlalchemy.sql.elements import BinaryExpression

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_repository import audit_repository
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

    audit_repository.get_all(
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
