import pytest
from app.models.user import User


def test_edge_case_duplicate_username(client):
    """Verify that registering the same username twice returns 409 Conflict."""
    payload = {"username": "dupuser", "email": "dup1@example.com", "password": "Password@123"}
    res = client.post("/api/v1/users", json=payload)
    assert res.status_code == 201

    res = client.post("/api/v1/users", json=payload)
    assert res.status_code == 409
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "DUPLICATE_USER"
    assert "Username already exists" in res.json()["error"]["message"]


def test_edge_case_duplicate_email(client):
    """Verify that registering the same email twice returns 409 Conflict."""
    payload1 = {"username": "user1", "email": "sameemail@example.com", "password": "Password@123"}
    payload2 = {"username": "user2", "email": "sameemail@example.com", "password": "Password@123"}
    res1 = client.post("/api/v1/users", json=payload1)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/users", json=payload2)
    assert res2.status_code == 409
    assert res2.json()["success"] is False
    assert res2.json()["error"]["code"] == "DUPLICATE_USER"
    assert "Email already exists" in res2.json()["error"]["message"]


def test_edge_case_missing_fields(client):
    """Verify that omitting required fields returns 422 Unprocessable Entity."""
    payload = {"username": "missingfields"}
    res = client.post("/api/v1/users", json=payload)
    assert res.status_code == 422
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_edge_case_blank_payload(client):
    """Verify that sending a blank/empty JSON object payload returns 422."""
    res = client.post("/api/v1/users", json={})
    assert res.status_code == 422
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_edge_case_malformed_json(client):
    """Verify that sending malformed JSON syntax is caught gracefully."""
    res = client.post(
        "/api/v1/users",
        content='{"username": "malformed", "email": "bad", ',
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code in [400, 422]
    assert res.json()["success"] is False


def test_edge_case_sql_injection_attempt(client):
    """Verify that SQL injection strings are safely parameterized and do not cause execution/crashes."""
    injection_strings = [
        "admin' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT NULL, NULL, NULL --",
    ]
    for sql in injection_strings:
        # 1. Register user with injection payload as username (should succeed or fail validation cleanly)
        res = client.post(
            "/api/v1/users",
            json={"username": sql[:50], "email": f"sql_{hash(sql)}@example.com", "password": "Password@123"},
        )
        # Should either successfully create user (treating username as string literal) or fail validation.
        # It must NOT raise a 500 database error.
        assert res.status_code in [201, 422]

        # 2. Forgot password request with injection payload as email
        res_forgot = client.post("/api/v1/password/forgot-password", json={"email": sql})
        # Should either be rejected as invalid email format (422) or treated as missing/unknown email (200)
        assert res_forgot.status_code in [200, 422]
        if res_forgot.status_code == 200:
            assert res_forgot.json()["success"] is True


def test_edge_case_unicode_inputs(client, db):
    """Verify that unicode characters are accepted and stored correctly in UTF-8."""
    unicode_username = "üserñamé_🚀"
    unicode_email = "unicode_test@example.com"
    
    res = client.post(
        "/api/v1/users",
        json={"username": unicode_username, "email": unicode_email, "password": "Password@123"},
    )
    assert res.status_code == 201
    
    # Verify exact unicode string is stored in DB
    user_in_db = db.query(User).filter_by(email=unicode_email).one()
    assert user_in_db.username == unicode_username


def test_edge_case_very_long_strings(client):
    """Verify that sending exceptionally long strings fails validation or is handled correctly."""
    long_username = "a" * 105
    res = client.post(
        "/api/v1/users",
        json={"username": long_username, "email": "long@example.com", "password": "Password@123"},
    )
    assert res.status_code == 422
    assert res.json()["success"] is False
