"""Server-side lifecycle management for administrator access tokens."""

import base64
import binascii
import json
from datetime import datetime, timezone as datetime_timezone

from django.utils import timezone

from .management_crypto import (
    decrypt_access_token,
    encrypt_access_token,
)
from .models import ManagementAuthToken


def _token_expiry(access_token):
    """Extract the expiry from a JWT issued by the trusted Auth Service."""
    if not isinstance(access_token, str):
        raise ValueError("Invalid administrator access token.")

    parts = access_token.split(".")

    if len(parts) != 3:
        raise ValueError("Invalid JWT structure.")

    try:
        payload_part = parts[1]

        if not payload_part or len(payload_part) > 8192:
            raise ValueError("Invalid JWT payload size.")

        padded = payload_part + "=" * (-len(payload_part) % 4)

        decoded = base64.b64decode(
            padded,
            altchars=b"-_",
            validate=True,
        )

        payload = json.loads(decoded)

        if not isinstance(payload, dict):
            raise ValueError("Invalid JWT payload.")

        exp = payload.get("exp")

        if type(exp) is not int or exp <= 0:
            raise ValueError("Invalid JWT expiry.")

        expires_at = datetime.fromtimestamp(
            exp,
            tz=datetime_timezone.utc,
        )

    except (
        ValueError,
        TypeError,
        OverflowError,
        UnicodeError,
        binascii.Error,
    ) as exc:
        raise ValueError("Invalid JWT expiry.") from exc

    if expires_at <= timezone.now():
        raise ValueError("Administrator access token has expired.")

    return expires_at


def store_management_token(session_key, access_token):
    """Encrypt and store an administrator JWT for a server-side session."""
    if not isinstance(session_key, str) or not session_key:
        raise ValueError("A valid session key is required.")

    expires_at = _token_expiry(access_token)
    encrypted = encrypt_access_token(access_token)

    ManagementAuthToken.objects.update_or_create(
        session_key=session_key,
        defaults={
            "encrypted_access_token": encrypted,
            "expires_at": expires_at,
        },
    )


def get_management_token(session_key):
    """Return a valid decrypted token, or None if unavailable."""
    if not session_key:
        return None

    record = ManagementAuthToken.objects.filter(
        session_key=session_key,
    ).first()

    if record is None:
        return None

    if record.expires_at <= timezone.now():
        record.delete()
        return None

    try:
        return decrypt_access_token(
            record.encrypted_access_token
        )
    except ValueError:
        record.delete()
        return None


def delete_management_token(session_key):
    """Remove the token associated with an administrator session."""
    if session_key:
        ManagementAuthToken.objects.filter(
            session_key=session_key,
        ).delete()
