"""
Authentication route tests.

These use the local SQLite test database from conftest.py, not Supabase.
"""


def test_register_user_succeeds(client) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": "Test12345"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "student@example.com"
    assert "password_hash" not in body


def test_duplicate_email_is_rejected(client) -> None:
    payload = {"email": "student@example.com", "password": "Test12345"}

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 400


def test_login_succeeds_with_correct_password(client) -> None:
    client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": "Test12345"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "Test12345"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client) -> None:
    client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": "Test12345"},
    )

    response = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": "Wrong12345"},
    )

    assert response.status_code == 401
