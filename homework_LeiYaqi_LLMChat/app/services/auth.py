from __future__ import annotations

import secrets
from typing import Any

import redis

from ..redis_client import get_redis
from ..security import Tokens, create_access_token, new_refresh_token
from ..settings import get_settings
from .users import get_user_by_id


def _refresh_key(token: str) -> str:
    return f"refresh:{token}"


def issue_tokens(user_id: str, login: str) -> Tokens:
    s = get_settings()
    r = get_redis()
    refresh = new_refresh_token()
    r.set(_refresh_key(refresh), user_id, ex=s.refresh_ttl_seconds)
    access = create_access_token(subject=user_id, extra={"login": login})
    return Tokens(access_token=access, refresh_token=refresh)


def refresh_access_token(refresh_token: str) -> str:
    r = get_redis()
    user_id = r.get(_refresh_key(refresh_token))
    if not user_id:
        raise KeyError("invalid_refresh")
    user = get_user_by_id(user_id)
    if user is None:
        raise KeyError("user_not_found")
    return create_access_token(subject=user_id, extra={"login": str(user.get("login", ""))})


def revoke_refresh_token(refresh_token: str) -> None:
    r = get_redis()
    r.delete(_refresh_key(refresh_token))


def new_oauth_state() -> str:
    return secrets.token_urlsafe(24)


def store_oauth_state(state: str) -> None:
    r = get_redis()
    r.set(f"oauth_state:{state}", "1", ex=600)


def consume_oauth_state(state: str) -> bool:
    r = get_redis()
    key = f"oauth_state:{state}"
    ok = r.get(key) is not None
    if ok:
        r.delete(key)
    return ok

