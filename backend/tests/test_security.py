"""
Tests for standalone security helpers.

These tests do not touch the database or R2. They prove the small cryptographic
building blocks behave the way the routes expect.
"""

import pytest

from app.security import (
    decrypt_file_bytes,
    decrypt_file_key,
    encrypt_file_bytes,
    encrypt_file_key,
    generate_encryption_key,
    generate_random_token,
    hash_token,
)


def test_generate_random_token_returns_different_non_empty_values() -> None:
    token_one = generate_random_token()
    token_two = generate_random_token()

    assert token_one
    assert token_two
    assert token_one != token_two


def test_hash_token_is_deterministic() -> None:
    token = "sample-share-token"

    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token


def test_aes_gcm_encrypt_decrypt_roundtrip() -> None:
    plaintext = b"hello secure file"
    file_key = generate_encryption_key()

    encrypted_bytes, nonce = encrypt_file_bytes(plaintext, file_key)
    wrapped_key = encrypt_file_key(file_key)
    unwrapped_key = decrypt_file_key(wrapped_key)
    decrypted_bytes = decrypt_file_bytes(encrypted_bytes, unwrapped_key, nonce)

    assert encrypted_bytes != plaintext
    assert decrypted_bytes == plaintext


def test_decrypting_with_wrong_key_fails() -> None:
    plaintext = b"this should not decrypt with the wrong key"
    correct_key = generate_encryption_key()
    wrong_key = generate_encryption_key()

    encrypted_bytes, nonce = encrypt_file_bytes(plaintext, correct_key)

    with pytest.raises(Exception):
        decrypt_file_bytes(encrypted_bytes, wrong_key, nonce)
