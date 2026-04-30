"""
File route tests.

R2 is mocked with an in-memory dictionary so tests do not need real Cloudflare
credentials and do not upload real objects.
"""

from conftest import login_headers, register_user


def test_authenticated_upload_creates_metadata(client, monkeypatch) -> None:
    stored_objects = {}

    def fake_upload(object_key: str, file_bytes: bytes, content_type: str) -> None:
        stored_objects[object_key] = file_bytes

    monkeypatch.setattr("app.routes.file_routes.upload_encrypted_file", fake_upload)

    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")

    response = client.post(
        "/files/upload",
        headers=headers,
        files={"uploaded_file": ("notes.txt", b"hello file", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "notes.txt"
    assert body["file_size"] == len(b"hello file")
    assert stored_objects


def test_unauthenticated_get_files_is_rejected(client) -> None:
    response = client.get("/files")

    assert response.status_code == 401


def test_get_files_returns_only_owned_files(client, monkeypatch) -> None:
    def fake_upload(object_key: str, file_bytes: bytes, content_type: str) -> None:
        return None

    monkeypatch.setattr("app.routes.file_routes.upload_encrypted_file", fake_upload)

    register_user(client, "owner@example.com")
    owner_headers = login_headers(client, "owner@example.com")
    register_user(client, "other@example.com")
    other_headers = login_headers(client, "other@example.com")

    owner_upload = client.post(
        "/files/upload",
        headers=owner_headers,
        files={"uploaded_file": ("owner.txt", b"owner", "text/plain")},
    )
    other_upload = client.post(
        "/files/upload",
        headers=other_headers,
        files={"uploaded_file": ("other.txt", b"other", "text/plain")},
    )

    response = client.get("/files", headers=owner_headers)
    ids = {item["id"] for item in response.json()}

    assert response.status_code == 200
    assert owner_upload.json()["id"] in ids
    assert other_upload.json()["id"] not in ids


def test_owner_download_route_works_with_mocked_r2(client, monkeypatch) -> None:
    stored_objects = {}

    def fake_upload(object_key: str, file_bytes: bytes, content_type: str) -> None:
        stored_objects[object_key] = file_bytes

    def fake_download(object_key: str) -> bytes:
        return stored_objects[object_key]

    monkeypatch.setattr("app.routes.file_routes.upload_encrypted_file", fake_upload)
    monkeypatch.setattr("app.routes.file_routes.download_encrypted_file", fake_download)

    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")

    upload_response = client.post(
        "/files/upload",
        headers=headers,
        files={"uploaded_file": ("download.txt", b"download me", "text/plain")},
    )
    file_id = upload_response.json()["id"]

    response = client.get(f"/files/{file_id}/download", headers=headers)

    assert response.status_code == 200
    assert response.content == b"download me"


def test_soft_delete_hides_file(client, monkeypatch) -> None:
    stored_objects = {}

    def fake_upload(object_key: str, file_bytes: bytes, content_type: str) -> None:
        stored_objects[object_key] = file_bytes

    def fake_delete(object_key: str) -> None:
        stored_objects.pop(object_key, None)

    monkeypatch.setattr("app.routes.file_routes.upload_encrypted_file", fake_upload)
    monkeypatch.setattr("app.routes.file_routes.delete_encrypted_file", fake_delete)

    register_user(client, "owner@example.com")
    headers = login_headers(client, "owner@example.com")

    upload_response = client.post(
        "/files/upload",
        headers=headers,
        files={"uploaded_file": ("delete.txt", b"delete me", "text/plain")},
    )
    file_id = upload_response.json()["id"]

    delete_response = client.delete(f"/files/{file_id}", headers=headers)
    list_response = client.get("/files", headers=headers)

    assert delete_response.status_code == 200
    assert all(item["id"] != file_id for item in list_response.json())
