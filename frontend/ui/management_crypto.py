"""Authenticated encryption for administrator API tokens."""

import os

from cryptography.fernet import Fernet, InvalidToken


def _get_cipher():
    """Load the configured Fernet key without generating a replacement."""
    key = os.environ.get("MANAGEMENT_TOKEN_ENCRYPTION_KEY")

    if not key:
        raise RuntimeError(
            "MANAGEMENT_TOKEN_ENCRYPTION_KEY must be configured."
        )

    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise RuntimeError(
            "MANAGEMENT_TOKEN_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_access_token(token):
    """Encrypt a nonempty JWT for server-side database storage."""
    if not isinstance(token, str) or not token:
        raise ValueError("A nonempty access token is required.")

    return _get_cipher().encrypt(
        token.encode("utf-8")
    ).decode("ascii")


def decrypt_access_token(encrypted_token):
    """Decrypt a previously encrypted administrator JWT."""
    if not isinstance(encrypted_token, str) or not encrypted_token:
        raise ValueError("A nonempty encrypted token is required.")

    try:
        return _get_cipher().decrypt(
            encrypted_token.encode("ascii")
        ).decode("utf-8")
    except (InvalidToken, UnicodeError, ValueError) as exc:
        raise ValueError(
            "Unable to decrypt administrator access token."
        ) from exc
