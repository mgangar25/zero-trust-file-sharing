"""
Storage abstraction layer.

The rest of the app should call these functions instead of talking directly to
Cloudflare R2. That makes it easier to swap local storage, R2, or test doubles
without rewriting route logic.
"""

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class StorageError(Exception):
    """
    Generic storage error used by route handlers.

    We intentionally avoid putting access keys, endpoint details, or raw provider
    errors into API responses. Routes can catch StorageError and return a safe
    message to the client.
    """


def get_r2_client():
    """
    Create a boto3 client configured for Cloudflare R2.

    A bucket is a private container for objects, similar to a top-level folder in
    object storage. An object key is the path/name of one stored object inside
    that bucket, such as users/<user_id>/files/<file_id>/report.pdf.

    Cloudflare R2 supports the S3-compatible API. That means boto3, Amazon's S3
    Python library, can also talk to R2 when we provide R2's endpoint URL and R2
    access keys from .env.
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def upload_encrypted_file(
    object_key: str,
    file_bytes: bytes,
    content_type: str,
) -> None:
    """
    Upload file bytes to Cloudflare R2.

    The route layer encrypts plaintext with AES-GCM before calling this helper.
    That separation keeps storage simple: it receives bytes and stores them, but
    it does not need to know how encryption works.
    """
    try:
        get_r2_client().put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type or "application/octet-stream",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("Could not upload file to object storage.") from exc


def download_encrypted_file(object_key: str) -> bytes:
    """
    Download file bytes from Cloudflare R2.

    These bytes are encrypted ciphertext. The route/service layer decrypts them
    only after authentication and ownership checks pass.
    """
    try:
        response = get_r2_client().get_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=object_key,
        )
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("Could not download file from object storage.") from exc


def delete_encrypted_file(object_key: str) -> None:
    """
    Delete an object from Cloudflare R2.

    Database soft delete and object storage delete are different operations:
    the database row records file metadata for the app, while R2 holds the actual
    uploaded bytes. This function removes the bytes from object storage.
    """
    try:
        get_r2_client().delete_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=object_key,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("Could not delete file from object storage.") from exc
