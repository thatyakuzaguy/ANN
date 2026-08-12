from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from secrets import token_bytes
from typing import Any

try:
    import jwt
except ModuleNotFoundError:
    jwt = None


TOKEN_ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 60


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    algorithm, raw_salt, raw_digest = stored.split("$", 2)
    if algorithm != "pbkdf2_sha256":
        return False
    salt = base64.b64decode(raw_salt.encode())
    expected = base64.b64decode(raw_digest.encode())
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return hmac.compare_digest(actual, expected)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _fallback_jwt_encode(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": TOKEN_ALGORITHM, "typ": "JWT"}
    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_base64url_encode(signature)}"


def _fallback_jwt_decode(token: str, secret: str) -> dict[str, Any]:
    encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual = _base64url_decode(encoded_signature)
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Token signature is invalid")
    payload = json.loads(_base64url_decode(encoded_payload).decode("utf-8"))
    expires_at = payload.get("exp")
    if isinstance(expires_at, int) and expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token has expired")
    return payload


def issue_token(subject: str) -> str:
    secret = os.environ.get("JWT_SECRET", "change-me")
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
    }
    if jwt is None:
        return _fallback_jwt_encode(payload, secret)
    return jwt.encode(payload, secret, algorithm=TOKEN_ALGORITHM)


def decode_token(token: str) -> str:
    secret = os.environ.get("JWT_SECRET", "change-me")
    if jwt is None:
        payload = _fallback_jwt_decode(token, secret)
    else:
        payload = jwt.decode(token, secret, algorithms=[TOKEN_ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise ValueError("Token subject is invalid")
    return subject
