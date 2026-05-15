from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

import jwt
from passlib.context import CryptContext

from .settings import get_settings


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
pbkdf2_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    try:
        return bcrypt_context.hash(password)
    except Exception:
        return pbkdf2_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt_context.verify(password, password_hash)
    except Exception:
        try:
            return pbkdf2_context.verify(password, password_hash)
        except Exception:
            return False


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    s = get_settings()
    if not str(s.jwt_secret or "").strip():
        raise RuntimeError("JWT_SECRET is required")
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + s.access_token_ttl_seconds,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    s = get_settings()
    if not str(s.jwt_secret or "").strip():
        raise RuntimeError("JWT_SECRET is required")
    payload = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("invalid_token_type")
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)
