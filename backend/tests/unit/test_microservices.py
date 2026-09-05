from fastapi.testclient import TestClient

from services.api_gateway.main import app as gateway_app
from services.audit_service.main import app as audit_app
from services.auth_service.main import app as auth_app
from services.notification_service.main import app as notification_app
from services.ticket_service.main import app as ticket_app
from services.workflow_service.main import app as workflow_app


def test_api_gateway_health():
    client = TestClient(gateway_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_auth_service_health():
    client = TestClient(auth_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_ticket_service_health():
    client = TestClient(ticket_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_workflow_service_health():
    client = TestClient(workflow_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_notification_service_health():
    client = TestClient(notification_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_audit_service_health():
    client = TestClient(audit_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"


def test_notification_service_send_sms(mocker):
    mocker.patch(
        "services.notification_service.main.notification_service.send_sms",
        return_value=True,
    )
    client = TestClient(notification_app)
    response = client.post(
        "/api/v1/notifications/send-sms",
        json={"phone_number": "+1234567890", "message": "Test microservice message"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["success"] is True
