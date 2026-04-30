"""
SQLAlchemy database models.

Each class in this file represents one database table. The fields describe the
columns, and relationships describe how tables connect to each other.
"""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    """
    Create a random UUID string for primary keys.

    UUID-style strings are harder to guess than auto-incrementing numbers, which
    is helpful for a security-focused project.
    """
    return str(uuid.uuid4())


class User(Base):
    """
    Stores registered users.

    We store a password hash, never the real password. If the database leaked,
    attackers should not immediately see user passwords.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships make it easy to navigate from one user to their files and
    # share links in Python code.
    files = relationship("File", back_populates="owner")
    share_links = relationship("ShareLink", back_populates="owner")


class File(Base):
    """
    Stores metadata about uploaded files.

    The actual encrypted file bytes will eventually live in Cloudflare R2. This
    table stores the metadata needed to find, decrypt, and display the file.
    """

    __tablename__ = "files"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)

    # Later this will be the object path/key inside Cloudflare R2.
    r2_object_key = Column(String(500), nullable=False, unique=True)

    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(255), nullable=True)

    # AES-GCM uses a nonce during encryption. We will save it once real
    # encryption is implemented. It is nullable for the current metadata-only
    # checkpoint because no encrypted bytes are being created yet.
    encryption_nonce = Column(String(255), nullable=True)

    # In a stronger future version, each file can have its own encryption key.
    # This column will store that file key after it has been safely encrypted.
    # It is nullable for now because this step does not implement encryption.
    encrypted_file_key = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="files")
    share_links = relationship("ShareLink", back_populates="file")
    access_logs = relationship("AccessLog", back_populates="file")


class ShareLink(Base):
    """
    Stores temporary links that allow file access without logging in.

    The public token itself is not stored. We store only a hash of it, similar to
    password storage, so a database leak does not reveal active share links.
    """

    __tablename__ = "share_links"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=False, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    token_hash = Column(String(255), nullable=False, unique=True, index=True)

    # Optional password protection for a share link. Null means no password.
    password_hash = Column(String(255), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_downloads = Column(Integer, nullable=True)
    download_count = Column(Integer, nullable=False, default=0)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    file = relationship("File", back_populates="share_links")
    owner = relationship("User", back_populates="share_links")
    access_logs = relationship("AccessLog", back_populates="share_link")


class AccessLog(Base):
    """
    Stores audit events for share-link access attempts.

    Audit logs are important in zero-trust systems because we want visibility
    into allowed and denied access, not just successful downloads.
    """

    __tablename__ = "access_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)

    # These are nullable because some failed attempts may not map cleanly to a
    # real share link or file, such as a completely invalid token.
    share_link_id = Column(String, ForeignKey("share_links.id"), nullable=True, index=True)
    file_id = Column(String, ForeignKey("files.id"), nullable=True, index=True)

    # Example event_type values: "share_view", "download", "password_check".
    event_type = Column(String(100), nullable=False)

    # Example status values: "success", "denied", "error".
    status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    share_link = relationship("ShareLink", back_populates="access_logs")
    file = relationship("File", back_populates="access_logs")
