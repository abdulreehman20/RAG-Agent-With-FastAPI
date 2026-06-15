"""Tests for POST /auth/signup, POST /auth/login, GET /auth/me."""

from __future__ import annotations

from starlette.testclient import TestClient

AUTH = "/api/v1/auth"


def _signup_body(email: str = "user@example.com", password: str = "password1", full_name: str = "Test User") -> dict:
    return {"email": email, "password": password, "full_name": full_name}


def test_signup_returns_201_and_user(client: TestClient) -> None:
    r = client.post(f"{AUTH}/signup", json=_signup_body())
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert isinstance(data["id"], int)


def test_signup_duplicate_email_returns_400_with_code(client: TestClient) -> None:
    body = _signup_body(email="dup@example.com")
    assert client.post(f"{AUTH}/signup", json=body).status_code == 201
    r = client.post(f"{AUTH}/signup", json=body)
    assert r.status_code == 400
    err = r.json()["detail"]
    assert err["code"] == "EMAIL_ALREADY_REGISTERED"
    assert "message" in err


def test_login_success_returns_token(client: TestClient) -> None:
    client.post(f"{AUTH}/signup", json=_signup_body(email="login@example.com", password="hunter22xx"))
    r = client.post(
        f"{AUTH}/login",
        json={"email": "login@example.com", "password": "hunter22xx"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"
    assert len(data["access_token"]) > 20


def test_login_wrong_password_returns_401_with_code(client: TestClient) -> None:
    client.post(f"{AUTH}/signup", json=_signup_body(email="pw@example.com", password="correctpass1"))
    r = client.post(
        f"{AUTH}/login",
        json={"email": "pw@example.com", "password": "wrongpassword"},
    )
    assert r.status_code == 401
    err = r.json()["detail"]
    assert err["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    r = client.post(
        f"{AUTH}/login",
        json={"email": "nobody@example.com", "password": "whatever11"},
    )
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_me_without_authorization_returns_401(client: TestClient) -> None:
    r = client.get(f"{AUTH}/me")
    assert r.status_code == 401
    err = r.json()["detail"]
    assert err["code"] == "AUTH_REQUIRED"


def test_me_with_valid_bearer_returns_current_user(client: TestClient) -> None:
    client.post(
        f"{AUTH}/signup",
        json=_signup_body(email="me@example.com", full_name="Me User"),
    )
    login = client.post(
        f"{AUTH}/login",
        json={"email": "me@example.com", "password": "password1"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    r = client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"
    assert data["is_active"] is True


def test_me_with_malformed_token_returns_401(client: TestClient) -> None:
    r = client.get(f"{AUTH}/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "TOKEN_INVALID"
