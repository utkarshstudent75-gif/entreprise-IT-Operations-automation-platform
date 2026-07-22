import pytest
from fastapi import status
from app.models.user import User
from app.services.user_service import user_service
from app.auth.providers.local import LocalAuthenticationProvider
from app.core.config import settings


def test_unauthorized_access_to_protected_endpoints(client):
    # Tickets endpoint
    response = client.get("/api/v1/tickets")
    assert response.status_code == 401
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

    # Workflows endpoint
    response = client.get("/api/v1/workflows")
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    response = client.get(
        "/api/v1/tickets",
        headers={"Authorization": "Bearer invalid_jwt_token_value"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_successful_local_login_and_token_access(client, db):
    # 1. Create a user
    user_service.pwd_context = user_service.pwd_context  # restore context
    hashed_password = user_service._hash_password("Password@123")
    user = User(
        username="integration_user",
        email="integration@example.com",
        hashed_password=hashed_password,
        roles="HelpDesk"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. Login via API
    response = client.post(
        "/api/v1/users/login",
        json={"username_or_email": "integration@example.com", "password": "Password@123"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    token = json_data["data"]["access_token"]
    assert token is not None

    # 3. Access protected tickets API using the token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/tickets", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "coming soon"}


def test_role_based_access_control(client, db):
    provider = LocalAuthenticationProvider()
    
    # Create HelpDesk user
    helpdesk = User(
        username="user_helpdesk",
        email="helpdesk@example.com",
        hashed_password="pwd",
        roles="HelpDesk"
    )
    # Create Admin user
    admin = User(
        username="user_admin",
        email="admin_role@example.com",
        hashed_password="pwd",
        roles="Admin"
    )
    db.add(helpdesk)
    db.add(admin)
    db.commit()
    db.refresh(helpdesk)
    db.refresh(admin)

    helpdesk_token = provider.create_access_token(user_id=helpdesk.id)
    admin_token = provider.create_access_token(user_id=admin.id)

    # 1. HelpDesk user requests /admin (Requires Admin) -> Expect 403
    response = client.get(
        "/api/v1/admin",
        headers={"Authorization": f"Bearer {helpdesk_token}"}
    )
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # 2. Admin user requests /admin -> Expect 200
    response = client.get(
        "/api/v1/admin",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
