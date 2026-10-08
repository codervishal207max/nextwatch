from fastapi.testclient import TestClient

from app.database.connection import Base, engine
from app.main import app


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_register_login_and_get_current_user() -> None:
    reset_database()
    client = TestClient(app)
    registration = client.post(
        "/api/auth/register",
        json={"name": "Alex Reader", "email": "ALEX@EXAMPLE.COM", "password": "safe-password-123"},
    )

    assert registration.status_code == 201
    assert registration.json()["email"] == "alex@example.com"
    assert "hashed_password" not in registration.json()

    login = client.post(
        "/api/auth/login",
        json={"email": "alex@example.com", "password": "safe-password-123"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]
    current_user = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})

    assert current_user.status_code == 200
    assert current_user.json()["name"] == "Alex Reader"


def test_registration_rejects_duplicate_email_and_short_password() -> None:
    reset_database()
    client = TestClient(app)
    payload = {"name": "Alex Reader", "email": "alex@example.com", "password": "safe-password-123"}

    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert client.post("/api/auth/register", json={**payload, "email": "new@example.com", "password": "short"}).status_code == 422
