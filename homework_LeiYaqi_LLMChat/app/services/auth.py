from __future__ import annotations

import secrets

from ..redis_client import get_redis
from ..security import Tokens, create_access_token, new_refresh_token
from ..settings import get_settings
from .users import get_user_by_id


def _refresh_key(token: str) -> str:
    return f"refresh:{token}"


async def issue_tokens(user_id: str, login: str) -> Tokens:
    s = get_settings()
    r = get_redis()
    refresh = new_refresh_token()
    await r.set(_refresh_key(refresh), user_id, ex=s.refresh_ttl_seconds)
    access = create_access_token(subject=user_id, extra={"login": login})
    return Tokens(access_token=access, refresh_token=refresh)


async def refresh_access_token(refresh_token: str) -> str:
    r = get_redis()
    user_id = await r.get(_refresh_key(refresh_token))
    if not user_id:
        raise KeyError("invalid_refresh")
    user = await get_user_by_id(str(user_id))
    if user is None:
        raise KeyError("user_not_found")
    return create_access_token(subject=str(user_id), extra={"login": str(user.get("login", ""))})


async def revoke_refresh_token(refresh_token: str) -> None:
    r = get_redis()
    await r.delete(_refresh_key(refresh_token))


def new_oauth_state() -> str:
    return secrets.token_urlsafe(24)


async def store_oauth_state(state: str) -> None:
    r = get_redis()
    await r.set(f"oauth_state:{state}", "1", ex=600)


async def consume_oauth_state(state: str) -> bool:
    r = get_redis()
    key = f"oauth_state:{state}"
    ok = (await r.get(key)) is not None
    if ok:
        await r.delete(key)
    return ok
