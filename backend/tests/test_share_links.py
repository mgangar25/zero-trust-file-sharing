"""
Share-link route tests.

These tests mock R2 but still exercise the real database, JWT auth, AES-GCM
helpers, token hashing, password checks, revocation, and audit logging.
"""

from app import models
from app.database import SessionLocal
from app.security import hash_token

from conftest import login_headers, register_user


def upload_test_file(client, headers, monkeypatch, content: bytes = b"shared file"):
    """Upload one encrypted test file while storing R2 bytes in memory."""
    stored_objects = {}

    def fake_upload(object_key: str, file_bytes: bytes, content_type: str) -> None:
        stored_objects[object_key] = file_bytes

    def fake_download(object_key: str) -> bytes:
        return stored_objects[object_key]

    def fake_delete(object_key: str) -> None:
        stored_objects.pop(object_key, None)

    monkeypatch.setattr("app.routes.file_routes.upload_encrypted_file", fake_upload)
    monkeypatch.setattr("app.routes.file_routes.download_encrypted_file", fake_download)
    monkeypatch.setattr("app.routes.file_routes.delete_encrypted_file", fake_delete)
    monkeypatch.setattr("app.routes.share_routes.download_encrypted_file", fake_download)

    response = client.post(
        "/files/upload",
        headers=headers,
        files={"uploaded_file": ("shared.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    return response.json(), stored_objects


def create_share(client, headers, file_id: str, **overrides):
    """Create a share link with sensible defaults for tests."""
    payload = {
        "expires_in_minutes": 30,
        "max_downloads": None,
        "password": None,
    }
    payload.update(overrides)

    response = client.post(f"/share/files/{file_id}", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_owner_can_create_share_link_and_raw_token_is_not_stored(client, monkeypatch) -> None:
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch)

    share = create_share(client, headers, uploaded_file["id"])

    assert share["raw_token"]
    assert share["file_id"] == uploaded_file["id"]

    db = SessionLocal()
    try:
        stored_share = db.query(models.ShareLink).filter(models.ShareLink.id == share["id"]).first()
        assert stored_share is not None
        assert stored_share.token_hash == hash_token(share["raw_token"])
        assert stored_share.token_hash != share["raw_token"]
    finally:
        db.close()


def test_public_download_works_with_valid_token(client, monkeypatch) -> None:
    content = b"public share content"
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch, content=content)
    share = create_share(client, headers, uploaded_file["id"])

    response = client.post(f"/share/{share['raw_token']}/download", json={})

    assert response.status_code == 200
    assert response.content == content


def test_max_downloads_blocks_after_limit(client, monkeypatch) -> None:
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch)
    share = create_share(client, headers, uploaded_file["id"], max_downloads=1)

    first_response = client.post(f"/share/{share['raw_token']}/download", json={})
    second_response = client.post(f"/share/{share['raw_token']}/download", json={})

    assert first_response.status_code == 200
    assert second_response.status_code == 403


def test_password_protected_link_rejects_wrong_password(client, monkeypatch) -> None:
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch)
    share = create_share(client, headers, uploaded_file["id"], password="SharePass123")

    response = client.post(
        f"/share/{share['raw_token']}/download",
        json={"password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_revoked_link_blocks_download(client, monkeypatch) -> None:
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch)
    share = create_share(client, headers, uploaded_file["id"])

    revoke_response = client.delete(f"/share/{share['id']}", headers=headers)
    download_response = client.post(f"/share/{share['raw_token']}/download", json={})

    assert revoke_response.status_code == 200
    assert download_response.status_code == 403


def test_audit_logs_are_created_for_share_attempts(client, monkeypatch) -> None:
    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")
    uploaded_file, _ = upload_test_file(client, headers, monkeypatch)
    share = create_share(client, headers, uploaded_file["id"], password="SharePass123")

    client.post(
        f"/share/{share['raw_token']}/download",
        json={"password": "WrongPass123"},
    )
    client.post(
        f"/share/{share['raw_token']}/download",
        json={"password": "SharePass123"},
    )

    response = client.get("/audit", headers=headers)
    reasons = {item["reason"] for item in response.json()}

    assert response.status_code == 200
    assert "invalid_password" in reasons
    assert "success" in reasons
