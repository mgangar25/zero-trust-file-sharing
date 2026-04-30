"""
Pydantic schemas for request and response data.

Schemas control what shape of JSON the API accepts and returns. They are separate
from database models so we do not accidentally expose sensitive database fields
like password hashes or token hashes.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Request body for creating a new user account."""

    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Request body for logging in with email and password."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe user data returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    """Response returned after a successful login."""

    access_token: str
    token_type: str = "bearer"


class FileResponse(BaseModel):
    """File metadata returned to the owner."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    original_filename: str
    file_size: int
    mime_type: Optional[str] = None
    created_at: datetime
    deleted_at: Optional[datetime] = None


class ShareLinkCreate(BaseModel):
    """Request body for creating a temporary share link."""

    expires_in_minutes: int = Field(gt=0)
    max_downloads: Optional[int] = Field(default=None, ge=1)
    password: Optional[str] = Field(default=None, min_length=8)


class ShareLinkResponse(BaseModel):
    """
    Safe share-link data returned to the owner.

    token is optional because the raw share token should usually be shown only
    once, immediately after link creation. The database stores token_hash, not
    the raw token.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    file_id: str
    owner_id: str
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    download_count: int
    is_revoked: bool
    created_at: datetime


class ShareLinkCreateResponse(ShareLinkResponse):
    """
    Response returned only when a share link is first created.

    raw_token is shown once because the database stores only token_hash. If the
    owner loses this token, the safe option is to revoke the link and create a
    new one.
    """

    raw_token: str
    share_url: str


class ShareDownloadRequest(BaseModel):
    """Optional request body for downloading through a public share link."""

    password: Optional[str] = None


class AccessLogResponse(BaseModel):
    """Audit log data returned to a file owner."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    share_link_id: Optional[str] = None
    file_id: Optional[str] = None
    event_type: str
    status: str
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
