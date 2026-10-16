from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_tickets_endpoint_requires_authentication():
    response = client.get("/tickets/")
    assert response.status_code == 401


def test_ticket_creation_requires_authentication():
    response = client.post(
        "/tickets/",
        json={
            "subject": "Test ticket",
            "description": "Testing authentication",
            "category_id": 1
        }
    )
    assert response.status_code == 401


def test_ticket_details_require_authentication():
    response = client.get("/tickets/1")
    assert response.status_code == 401


def test_ticket_history_requires_authentication():
    response = client.get("/tickets/1/history")
    assert response.status_code == 401