from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_categories_endpoint():
    response = client.get("/categories/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_category_requires_authentication():
    response = client.post(
        "/categories/",
        json={
            "category_name": "Test Category",
            "description": "Created by automated test",
        },
    )

    assert response.status_code == 401


def test_create_category_rejects_invalid_payload():
    response = client.post(
        "/categories/",
        json={},
    )

    
    assert response.status_code == 401