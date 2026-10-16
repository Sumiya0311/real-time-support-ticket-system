from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.user import User

client = TestClient(app)


def test_register_requires_valid_data():
    response = client.post("/auth/register", json={})
    assert response.status_code == 422


def test_login_requires_valid_data():
    response = client.post("/auth/login", json={})
    assert response.status_code == 422


def test_login_with_invalid_email_format():
    response = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 422


def test_me_requires_authentication():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_register_rejects_duplicate_email():
    existing_user = MagicMock(spec=User)
    existing_user.email = "existing@example.com"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_user

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/auth/register",
            json={
                "full_name": "Test User",
                "email": "existing@example.com",
                "password": "StrongPassword123!",
            },
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Email is already registered"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_login_rejects_unknown_email():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"
    finally:
        app.dependency_overrides.pop(get_db, None)