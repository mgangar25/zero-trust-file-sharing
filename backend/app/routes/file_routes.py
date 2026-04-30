"""
File routes.

This step stores uploaded file bytes in Cloudflare R2 and stores file metadata
in Supabase PostgreSQL. Files are encrypted before they are stored in R2 and
decrypted only after owner authorization passes.
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.security import (
    decrypt_file_bytes,
    decrypt_file_key,
    encrypt_file_bytes,
    encrypt_file_key,
    generate_encryption_key,
)
from app.storage import (
    StorageError,
    delete_encrypted_file,
    download_encrypted_file,
    upload_encrypted_file,
)


router = APIRouter(prefix="/files", tags=["Files"])


def get_safe_filename(filename: str | None) -> str:
    """
    Convert a browser-provided filename into safe metadata.

    We are not saving files to local disk, but filenames can still appear in R2
    object keys and response headers. Path(...).name removes accidental folder
    paths, and the fallback avoids empty names.
    """
    safe_filename = Path(filename or "uploaded-file").name
    return safe_filename or "uploaded-file"


def build_object_key(user_id: str, file_id: str, filename: str) -> str:
    """
    Build the Cloudflare R2 object key for one uploaded file.

    Including user_id groups objects by owner, which makes storage easier to
    inspect and clean up. Including file_id prevents two files with the same
    filename from overwriting each other.
    """
    return f"users/{user_id}/files/{file_id}/{filename}"


def get_user_file_or_404(
    file_id: str,
    current_user: models.User,
    db: Session,
) -> models.File:
    """
    Find one active file owned by the current user.

    This helper prevents a common security mistake: trusting a file_id by itself.
    File ids are not permission. Every lookup must also check owner_id so one
    logged-in user cannot view or delete another user's file metadata.
    """
    file_record = (
        db.query(models.File)
        .filter(models.File.id == file_id)
        .filter(models.File.owner_id == current_user.id)
        .filter(models.File.deleted_at.is_(None))
        .first()
    )

    if file_record is None:
        # Returning 404 instead of 403 avoids confirming whether another user's
        # file id exists. That is a small but useful privacy/security habit.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File was not found.",
        )

    return file_record


@router.post(
    "/upload",
    response_model=schemas.FileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file_metadata(
    uploaded_file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.File:
    """
    Upload a file to Cloudflare R2 and save its metadata in Supabase.

    Security flow:
    - Read the uploaded plaintext bytes from the request.
    - Generate one random per-file AES-256 key.
    - Encrypt the file bytes with AES-GCM.
    - Encrypt/wrap the per-file key with MASTER_ENCRYPTION_KEY.
    - Upload only encrypted bytes to R2.
    - Save the encrypted file key and nonce in Supabase metadata.

    file_size stores the original plaintext size because that is what users
    expect to see in the UI. The encrypted object stored in R2 may be slightly
    larger because AES-GCM adds an authentication tag.

    Important:
    - We do not save the raw file locally.
    - We do not accept owner_id from the request body.
    - R2 receives ciphertext, not readable file contents.
    """
    file_bytes = await uploaded_file.read()
    file_size = len(file_bytes)

    # Do not accept owner_id from the request. The authenticated JWT decides who
    # owns the file, which prevents users from creating files under another
    # user's account.
    original_filename = get_safe_filename(uploaded_file.filename)

    file_id = models.generate_uuid()
    object_key = build_object_key(current_user.id, file_id, original_filename)

    file_key = generate_encryption_key()
    encrypted_file_bytes, encryption_nonce = encrypt_file_bytes(file_bytes, file_key)
    encrypted_file_key = encrypt_file_key(file_key)

    try:
        upload_encrypted_file(
            object_key=object_key,
            file_bytes=encrypted_file_bytes,
            # The object body is encrypted bytes, so octet-stream is more honest
            # than the original MIME type at the storage layer. The original MIME
            # type is still saved in the database for owner downloads.
            content_type="application/octet-stream",
        )
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="File could not be uploaded to storage. Please try again.",
        ) from exc

    file_record = models.File(
        id=file_id,
        owner_id=current_user.id,
        original_filename=original_filename,
        r2_object_key=object_key,
        file_size=file_size,
        mime_type=uploaded_file.content_type,
        encryption_nonce=encryption_nonce,
        encrypted_file_key=encrypted_file_key,
        deleted_at=None,
    )

    try:
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
    except SQLAlchemyError as exc:
        db.rollback()

        # If metadata saving fails after the R2 upload, try to remove the object
        # so storage does not keep an orphaned file. We still return a generic
        # database/storage consistency error without exposing internals.
        try:
            delete_encrypted_file(object_key)
        except StorageError:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File metadata could not be saved. Please try again.",
        ) from exc

    return file_record


@router.get("", response_model=list[schemas.FileResponse])
def list_files(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.File]:
    """
    Return the current user's file metadata.

    This is protected with get_current_user, so callers must send a valid JWT.
    Deleted files are hidden because deleted_at means the file should no longer
    appear in the normal user interface.
    """
    return (
        db.query(models.File)
        .filter(models.File.owner_id == current_user.id)
        .filter(models.File.deleted_at.is_(None))
        .order_by(models.File.created_at.desc())
        .all()
    )


@router.get("/{file_id}", response_model=schemas.FileResponse)
def get_file(
    file_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.File:
    """
    Return one file metadata record owned by the current user.

    The owner check is the key security rule here. Even if a user guesses another
    file id, they should not be able to read metadata for a file they do not own.
    """
    return get_user_file_or_404(file_id, current_user, db)


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """
    Download one file owned by the current user.

    This is owner-only download for now. Public temporary share-link downloads
    will come later and will have separate checks for expiration, revocation,
    download limits, optional passwords, and audit logging.

    R2 stores encrypted bytes. Only after the user is authenticated and confirmed
    as the file owner do we decrypt the per-file key and then decrypt the file
    bytes returned to the browser.
    """
    file_record = get_user_file_or_404(file_id, current_user, db)

    if not file_record.encryption_nonce or not file_record.encrypted_file_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Encryption metadata is missing for this file. "
                "Older metadata-only test files should be re-uploaded."
            ),
        )

    try:
        encrypted_file_bytes = download_encrypted_file(file_record.r2_object_key)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="File could not be downloaded from storage. Please try again.",
        ) from exc

    try:
        file_key = decrypt_file_key(file_record.encrypted_file_key)
        file_bytes = decrypt_file_bytes(
            encrypted_file_bytes,
            file_key,
            file_record.encryption_nonce,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File could not be decrypted. Please verify encryption metadata.",
        ) from exc

    encoded_filename = quote(file_record.original_filename)

    return Response(
        content=file_bytes,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Delete the stored object and soft-delete its metadata row.

    Soft delete means we set deleted_at instead of removing the row. This helps
    security and auditability because the system can later answer questions like
    "when was this file deleted?" or preserve relationships to future audit logs.

    R2 object deletion removes the uploaded bytes from object storage. We attempt
    the R2 delete before the database soft delete so the database does not say
    "deleted" while the object is still present in storage.
    """
    file_record = get_user_file_or_404(file_id, current_user, db)

    try:
        delete_encrypted_file(file_record.r2_object_key)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="File could not be deleted from storage. Please try again.",
        ) from exc

    file_record.deleted_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "File was soft-deleted successfully.",
        "file_id": file_record.id,
    }
