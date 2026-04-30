"""
Shared pytest setup for backend tests.

The real project uses Supabase PostgreSQL and Cloudflare R2. Tests should not
need real credentials or external services, so this file configures safe local
environment variables before the FastAPI app imports its settings.
"""

import base64
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# Set safe test-only environment variables before importing app modules.
# load_dotenv() will not override these values, so tests never need backend/.env.
TEST_DATABASE_PATH = Path("/tmp/zero_trust_file_sharing_tests/test_zero_trust.db")
TEST_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-not-for-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["R2_ACCOUNT_ID"] = "test-account"
os.environ["R2_ACCESS_KEY_ID"] = "test-access-key"
os.environ["R2_SECRET_ACCESS_KEY"] = "test-secret-key"
os.environ["R2_BUCKET_NAME"] = "test-bucket"
os.environ["R2_ENDPOINT_URL"] = "http://test-r2.local"
os.environ["MASTER_ENCRYPTION_KEY"] = base64.b64encode(b"0" * 32).decode()


from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    """
    Recreate all tables before each test.

    This keeps tests independent: a user or file created in one test cannot
    accidentally affect another test.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient for route tests."""
    with TestClient(app) as test_client:
        yield test_client


def register_user(client: TestClient, email: str, password: str = "Test12345") -> dict:
    """Small helper for tests that need a registered user."""
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def login_headers(client: TestClient, email: str, password: str = "Test12345") -> dict:
    """Return an Authorization header for a registered test user."""
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
