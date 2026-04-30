"""
Security helper functions that are not specific to login.

This file will grow as the project adds encrypted uploads, password-protected
share links, and secure downloads.
"""

import base64
import hashlib
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


AES_256_KEY_SIZE_BYTES = 32
AES_GCM_NONCE_SIZE_BYTES = 12


def generate_random_token() -> str:
    """
    Generate a random URL-safe token for share links.

    secrets.token_urlsafe() uses Python's cryptographically secure random number
    generator. That matters because share-link tokens must be very hard to guess.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash a share token before saving it to the database.

    This is similar to password storage: the user receives the raw token in the
    URL, but the database stores only a SHA-256 hash. If the database leaks, an
    attacker cannot directly use the stored value as a working share link.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _decode_master_encryption_key() -> bytes:
    """
    Decode the local development master key from base64 into bytes.

    The master key is stored in .env as text because environment variables are
    strings. AES-GCM needs bytes, so we decode it before use. config.py already
    validates the key at startup; this helper keeps encryption code readable.
    """
    return base64.b64decode(settings.MASTER_ENCRYPTION_KEY, validate=True)


def generate_encryption_key() -> bytes:
    """
    Generate one random AES-256 key for one file.

    Every file gets its own random file key. That way, if one file key were ever
    exposed, it would not automatically decrypt every other file in the system.
    """
    return secrets.token_bytes(AES_256_KEY_SIZE_BYTES)


def encrypt_file_key(file_key: bytes) -> str:
    """
    Encrypt, or "wrap", a per-file key with the master encryption key.

    We cannot store the raw file key in the database because that would make the
    encrypted R2 object much easier to decrypt after a database leak. Instead,
    the database stores a base64 string containing:

        12-byte AES-GCM nonce + encrypted file key bytes

    AES-GCM both encrypts data and authenticates it, which means decryption will
    fail if the ciphertext is tampered with.
    """
    master_key = _decode_master_encryption_key()
    nonce = secrets.token_bytes(AES_GCM_NONCE_SIZE_BYTES)
    encrypted_file_key = AESGCM(master_key).encrypt(nonce, file_key, None)
    return base64.b64encode(nonce + encrypted_file_key).decode("utf-8")


def decrypt_file_key(encrypted_file_key: str) -> bytes:
    """
    Decrypt a wrapped per-file key from the database.

    This reverses encrypt_file_key(). The server needs the original per-file key
    before it can decrypt the encrypted bytes downloaded from R2.
    """
    encrypted_payload = base64.b64decode(encrypted_file_key, validate=True)
    nonce = encrypted_payload[:AES_GCM_NONCE_SIZE_BYTES]
    ciphertext = encrypted_payload[AES_GCM_NONCE_SIZE_BYTES:]

    master_key = _decode_master_encryption_key()
    return AESGCM(master_key).decrypt(nonce, ciphertext, None)


def encrypt_file_bytes(file_bytes: bytes, file_key: bytes) -> tuple[bytes, str]:
    """
    Encrypt uploaded file bytes with AES-GCM.

    AES-GCM needs a fresh nonce for every encryption with the same key. We save
    the nonce in the database because it is required for decryption later. The
    nonce is not secret, but it must be unique for each encryption operation.

    Only encrypted bytes should be stored in Cloudflare R2.
    """
    nonce = secrets.token_bytes(AES_GCM_NONCE_SIZE_BYTES)
    encrypted_bytes = AESGCM(file_key).encrypt(nonce, file_bytes, None)
    nonce_b64 = base64.b64encode(nonce).decode("utf-8")

    return encrypted_bytes, nonce_b64


def decrypt_file_bytes(encrypted_bytes: bytes, file_key: bytes, nonce_b64: str) -> bytes:
    """
    Decrypt encrypted file bytes downloaded from R2.

    The owner receives the original plaintext bytes only after authentication,
    ownership checks, file-key unwrapping, and AES-GCM decryption all succeed.
    """
    nonce = base64.b64decode(nonce_b64, validate=True)
    return AESGCM(file_key).decrypt(nonce, encrypted_bytes, None)
