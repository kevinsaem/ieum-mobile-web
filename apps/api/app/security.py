import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return "scrypt${}${}".format(
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt_text, digest_text = encoded.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
    except (ValueError, TypeError):
        return False
    actual = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return hmac.compare_digest(actual, expected)


def _jwt_secret() -> str:
    secret = os.getenv("IEUM_JWT_SECRET")
    if not secret or len(secret) < 32:
        raise RuntimeError("IEUM_JWT_SECRET must be at least 32 characters")
    return secret


def create_access_token(*, user_id: str, role: str, organization_id: str | None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "organization_id": organization_id,
        "iat": now,
        "exp": now + timedelta(hours=8),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, object]:
    return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
