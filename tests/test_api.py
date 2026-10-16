from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Real-Time Support Ticket System API is running"
    }


def test_swagger_docs_available():
    response = client.get("/docs")

    assert response.status_code == 200


def test_openapi_schema_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()


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


def test_invalid_route_returns_404():
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404


def test_health_of_api_root():
    response = client.get("/")

    assert response.status_code == 200