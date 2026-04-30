"""
Application configuration.

Configuration values come from environment variables, usually stored in a local
`.env` file during development.
"""

import base64
import binascii
import os
from pathlib import Path

from dotenv import load_dotenv


# This points to backend/.env no matter where the server command is started.
# Keeping the path explicit avoids confusing bugs where Python looks for .env in
# the wrong folder.
ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"


# load_dotenv reads key/value pairs from backend/.env and makes them available
# through os.getenv(). This keeps secrets out of the source code.
#
# Important: real DATABASE_URL, JWT_SECRET_KEY, and Cloudflare R2 credentials
# should live in .env, not inside Python files and not in GitHub.
load_dotenv(dotenv_path=ENV_FILE_PATH)


def _get_required_env(name: str) -> str:
    """
    Read an environment variable that must be provided.

    Failing early with a clear message is safer than starting the API with a
    missing database URL or weak JWT secret.
    """
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Create backend/.env from .env.example and set a real value."
        )
    return value


def _get_optional_env(name: str, default: str) -> str:
    """
    Read an optional environment variable with a development-friendly default.

    Optional settings still load from .env when present, but the app can use a
    clear default for values that are not secrets.
    """
    return os.getenv(name) or default


def _get_positive_int_env(name: str, default: str) -> int:
    """
    Read an integer setting and validate that it is positive.

    ACCESS_TOKEN_EXPIRE_MINUTES controls security behavior, so a typo such as
    "abc" or "0" should produce a helpful startup error.
    """
    raw_value = _get_optional_env(name, default)

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a whole number.") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than 0.")

    return value


def _get_required_base64_key_env(name: str) -> str:
    """
    Read and validate a required 32-byte base64-encoded key.

    AES-256 needs 32 bytes of key material. We store the key as base64 text in
    .env because environment variables are strings, then decode it here only to
    check that it has the correct shape. The app keeps the setting as a string
    and security.py decodes it again when encryption is performed.
    """
    value = _get_required_env(name)

    try:
        decoded_key = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(f"{name} must be valid base64 text.") from exc

    if len(decoded_key) != 32:
        raise RuntimeError(f"{name} must decode to exactly 32 bytes.")

    return value


class Settings:
    """
    Central place for application settings.

    Keeping settings in one class makes it easier to see what the app needs and
    avoids scattering os.getenv() calls across many files.
    """

    # Supabase gives you a PostgreSQL connection string. Put that value in
    # DATABASE_URL inside your local .env file.
    DATABASE_URL: str = _get_required_env("DATABASE_URL")

    # JWT_SECRET_KEY is used to sign login tokens. If someone has this secret,
    # they could forge tokens, so never commit a real value to GitHub.
    JWT_SECRET_KEY: str = _get_required_env("JWT_SECRET_KEY")

    # HS256 is a common symmetric signing algorithm for JWTs. "Symmetric" means
    # the same secret is used to create and verify tokens.
    JWT_ALGORITHM: str = _get_optional_env("JWT_ALGORITHM", "HS256")

    # Controls how long a login token remains valid.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_positive_int_env(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )

    # FRONTEND_ORIGIN is the deployed frontend URL, such as the Vercel app URL.
    # It is optional during local development because main.py always allows the
    # local Next.js dev origins.
    FRONTEND_ORIGIN: str = _get_optional_env("FRONTEND_ORIGIN", "")

    # FRONTEND_URL was used earlier in the project. Keeping it as an optional
    # fallback avoids breaking existing local .env files while new deployments
    # can use the clearer FRONTEND_ORIGIN name.
    FRONTEND_URL: str = _get_optional_env("FRONTEND_URL", "http://localhost:5173")

    # MASTER_ENCRYPTION_KEY protects the per-file encryption keys during local
    # development. It must never be committed to GitHub because anyone with this
    # value and database access could decrypt file keys.
    #
    # Production systems should use a real key management service instead, such
    # as AWS KMS, GCP KMS, or a Cloudflare-managed key system. A KMS can rotate,
    # audit, and protect keys better than a plain .env value.
    MASTER_ENCRYPTION_KEY: str = _get_required_base64_key_env("MASTER_ENCRYPTION_KEY")

    # Cloudflare R2 stores uploaded file objects. R2 exposes an S3-compatible
    # API, so boto3 can talk to it using an endpoint URL and access keys.
    #
    # These values are required now that uploads write to R2. They are secrets
    # or deployment-specific settings, so keep them in backend/.env.
    R2_ACCOUNT_ID: str = _get_required_env("R2_ACCOUNT_ID")
    R2_ACCESS_KEY_ID: str = _get_required_env("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY: str = _get_required_env("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME: str = _get_required_env("R2_BUCKET_NAME")
    R2_ENDPOINT_URL: str = _get_required_env("R2_ENDPOINT_URL")


# A single settings object can be imported anywhere in the app.
settings = Settings()
