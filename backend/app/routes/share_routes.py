"""
Share-link routes.

Share links let a file owner grant limited public access to one encrypted file.
The recipient does not need to log in, but the token must still pass expiration,
revocation, download-count, and optional password checks.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user, hash_password, verify_password
from app.database import get_db
from app.security import (
    decrypt_file_bytes,
    decrypt_file_key,
    generate_random_token,
    hash_token,
)
from app.storage import StorageError, download_encrypted_file


router = APIRouter(prefix="/share", tags=["Share Links"])


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """
    Make database datetimes safe to compare with timezone-aware UTC values.

    Some database drivers return timezone-aware values, while others return
    naive values. Treating naive timestamps as UTC keeps comparisons predictable.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_owned_file_or_404(
    file_id: str,
    current_user: models.User,
    db: Session,
) -> models.File:
    """
    Find one active file owned by the authenticated user.

    A file id alone is not permission. Checking owner_id prevents one logged-in
    user from creating share links for another user's encrypted file.
    """
    file_record = (
        db.query(models.File)
        .filter(models.File.id == file_id)
        .filter(models.File.owner_id == current_user.id)
        .filter(models.File.deleted_at.is_(None))
        .first()
    )

    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File was not found.",
        )

    return file_record


def log_access_attempt(
    db: Session,
    request: Request,
    event_type: str,
    status_value: str,
    reason: str,
    share_link_id: str | None = None,
    file_id: str | None = None,
    commit: bool = True,
) -> models.AccessLog:
    """
    Save an audit log for a public share-link access attempt.

    Audit logs matter because secure file sharing needs visibility into both
    successful downloads and blocked attempts. We record the IP address and user
    agent when FastAPI provides them, but we never store passwords or tokens.
    """
    access_log = models.AccessLog(
        share_link_id=share_link_id,
        file_id=file_id,
        event_type=event_type,
        status=status_value,
        reason=reason,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.add(access_log)
    if commit:
        db.commit()

    return access_log


def reject_share_download(
    db: Session,
    request: Request,
    http_status: int,
    detail: str,
    reason: str,
    share_link: models.ShareLink | None = None,
    file_id: str | None = None,
) -> None:
    """
    Log a failed public download attempt and then raise an HTTP error.

    Keeping this pattern in one helper makes it harder to forget audit logging
    on one of the security failure branches.
    """
    log_access_attempt(
        db=db,
        request=request,
        event_type="download",
        status_value="failure",
        reason=reason,
        share_link_id=share_link.id if share_link else None,
        file_id=file_id,
    )

    raise HTTPException(status_code=http_status, detail=detail)


@router.post(
    "/files/{file_id}",
    response_model=schemas.ShareLinkCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_share_link(
    file_id: str,
    share_data: schemas.ShareLinkCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> schemas.ShareLinkCreateResponse:
    """
    Create a temporary share link for one owned file.

    The raw token is shown once in this response, but only token_hash is saved in
    the database. That means a database leak does not immediately reveal usable
    share URLs. If the owner loses the raw token, they should revoke this link
    and create a new one.
    """
    get_owned_file_or_404(file_id, current_user, db)

    raw_token = generate_random_token()
    token_hash = hash_token(raw_token)
    expires_at = utc_now() + timedelta(minutes=share_data.expires_in_minutes)

    share_link = models.ShareLink(
        file_id=file_id,
        owner_id=current_user.id,
        token_hash=token_hash,
        password_hash=hash_password(share_data.password) if share_data.password else None,
        expires_at=expires_at,
        max_downloads=share_data.max_downloads,
        download_count=0,
        is_revoked=False,
    )

    db.add(share_link)
    db.commit()
    db.refresh(share_link)

    return schemas.ShareLinkCreateResponse(
        id=share_link.id,
        file_id=share_link.file_id,
        owner_id=share_link.owner_id,
        expires_at=share_link.expires_at,
        max_downloads=share_link.max_downloads,
        download_count=share_link.download_count,
        is_revoked=share_link.is_revoked,
        created_at=share_link.created_at,
        raw_token=raw_token,
        share_url=f"/share/{raw_token}/download",
    )


@router.get("", response_model=list[schemas.ShareLinkResponse])
def list_share_links(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.ShareLink]:
    """
    List share links owned by the current user.

    The response schema intentionally excludes token_hash and password_hash. The
    owner can see link status and limits, but not the secrets behind the link.
    """
    return (
        db.query(models.ShareLink)
        .filter(models.ShareLink.owner_id == current_user.id)
        .order_by(models.ShareLink.created_at.desc())
        .all()
    )


@router.delete("/{share_id}")
def revoke_share_link(
    share_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Revoke a share link owned by the current user.

    Revoke is different from delete: we keep the row for auditability, but mark
    it unusable. Future download attempts with this token will be blocked.
    """
    share_link = (
        db.query(models.ShareLink)
        .filter(models.ShareLink.id == share_id)
        .filter(models.ShareLink.owner_id == current_user.id)
        .first()
    )

    if share_link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link was not found.",
        )

    share_link.is_revoked = True
    db.commit()

    return {
        "message": "Share link was revoked successfully.",
        "share_id": share_link.id,
    }


@router.post("/{token}/download")
def download_shared_file(
    token: str,
    request: Request,
    download_data: schemas.ShareDownloadRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> Response:
    """
    Public download route for a valid share token.

    The token gives limited access only to the linked file. It is not a login
    session and it cannot list other files. Every public attempt is audited when
    possible so owners can review successful and blocked access.
    """
    share_link = (
        db.query(models.ShareLink)
        .filter(models.ShareLink.token_hash == hash_token(token))
        .first()
    )

    if share_link is None:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_404_NOT_FOUND,
            detail="Share link was not found.",
            reason="not_found",
        )

    if share_link.is_revoked:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_403_FORBIDDEN,
            detail="Share link has been revoked.",
            reason="revoked",
            share_link=share_link,
            file_id=share_link.file_id,
        )

    if share_link.expires_at is not None and as_utc(share_link.expires_at) < utc_now():
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_403_FORBIDDEN,
            detail="Share link has expired.",
            reason="expired",
            share_link=share_link,
            file_id=share_link.file_id,
        )

    if (
        share_link.max_downloads is not None
        and share_link.download_count >= share_link.max_downloads
    ):
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_403_FORBIDDEN,
            detail="Share link download limit has been reached.",
            reason="max_downloads_reached",
            share_link=share_link,
            file_id=share_link.file_id,
        )

    if share_link.password_hash:
        if download_data is None or not download_data.password:
            reject_share_download(
                db=db,
                request=request,
                http_status=status.HTTP_401_UNAUTHORIZED,
                detail="Password is required for this share link.",
                reason="missing_password",
                share_link=share_link,
                file_id=share_link.file_id,
            )

        if not verify_password(download_data.password, share_link.password_hash):
            reject_share_download(
                db=db,
                request=request,
                http_status=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid share link password.",
                reason="invalid_password",
                share_link=share_link,
                file_id=share_link.file_id,
            )

    file_record = (
        db.query(models.File)
        .filter(models.File.id == share_link.file_id)
        .filter(models.File.deleted_at.is_(None))
        .first()
    )

    if file_record is None:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_404_NOT_FOUND,
            detail="Shared file was not found.",
            reason="file_not_found",
            share_link=share_link,
            file_id=share_link.file_id,
        )

    if not file_record.encryption_nonce or not file_record.encrypted_file_key:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption metadata is missing for this shared file.",
            reason="missing_encryption_metadata",
            share_link=share_link,
            file_id=file_record.id,
        )

    try:
        encrypted_file_bytes = download_encrypted_file(file_record.r2_object_key)
        file_key = decrypt_file_key(file_record.encrypted_file_key)
        file_bytes = decrypt_file_bytes(
            encrypted_file_bytes,
            file_key,
            file_record.encryption_nonce,
        )
    except StorageError as exc:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_502_BAD_GATEWAY,
            detail="Shared file could not be downloaded from storage.",
            reason="storage_error",
            share_link=share_link,
            file_id=file_record.id,
        )
    except Exception as exc:
        reject_share_download(
            db=db,
            request=request,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Shared file could not be decrypted.",
            reason="decrypt_failed",
            share_link=share_link,
            file_id=file_record.id,
        )

    share_link.download_count += 1
    log_access_attempt(
        db=db,
        request=request,
        event_type="download",
        status_value="success",
        reason="success",
        share_link_id=share_link.id,
        file_id=file_record.id,
        commit=False,
    )
    db.commit()

    encoded_filename = quote(file_record.original_filename)

    return Response(
        content=file_bytes,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )
