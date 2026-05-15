from __future__ import annotations

from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from ..schemas import LoginIn, RefreshIn, RegisterIn, TokensOut, UserOut
from ..settings import get_settings
from .auth import consume_oauth_state, issue_tokens, new_oauth_state, refresh_access_token, store_oauth_state
from .oauth_github import build_authorize_url, exchange_code, fetch_user
from .users import create_user, get_user_by_login, set_user_password, upsert_github_user, verify_user_password


async def register(payload: RegisterIn) -> UserOut:
    existing = await get_user_by_login(payload.login)
    if existing is not None:
        if existing.get("github_id") is not None and not str(existing.get("password_hash") or "").strip():
            ok = await set_user_password(str(existing["_id"]), payload.password)
            if not ok:
                raise HTTPException(status_code=500, detail="password_set_failed")
            return UserOut(id=str(existing["_id"]), login=str(existing.get("login", "")))
        raise HTTPException(status_code=409, detail="login_taken")
    u = await create_user(payload.login, payload.password)
    created = await get_user_by_login(payload.login)
    if created is None:
        raise HTTPException(status_code=500, detail="user_create_failed")
    if not verify_user_password(created, payload.password):
        raise HTTPException(status_code=500, detail="password_hash_failed")
    return UserOut(id=u["id"], login=u["login"])


async def login(payload: LoginIn) -> TokensOut:
    u = await get_user_by_login(payload.login)
    if u is None:
        raise HTTPException(status_code=401, detail="user_not_found")
    if not verify_user_password(u, payload.password):
        raise HTTPException(status_code=401, detail="wrong_password")
    tokens = await issue_tokens(str(u["_id"]), str(u.get("login", "")))
    return TokensOut(access_token=tokens.access_token, refresh_token=tokens.refresh_token, token_type=tokens.token_type)


async def refresh(payload: RefreshIn) -> dict[str, str]:
    try:
        access = await refresh_access_token(payload.refresh_token)
    except KeyError:
        raise HTTPException(status_code=401, detail="invalid_refresh")
    return {"access_token": access, "token_type": "bearer"}


def github_status(request: Request) -> dict[str, object]:
    s = get_settings()
    return {
        "has_jwt_secret": bool(str(s.jwt_secret or "").strip()),
        "has_github_client_id": bool(s.github_client_id),
        "has_github_client_secret": bool(s.github_client_secret),
        "request_base_url": str(request.base_url).rstrip("/"),
        "settings_base_url": str(s.base_url).rstrip("/"),
    }


async def github_login(request: Request) -> dict[str, str]:
    try:
        state = new_oauth_state()
        await store_oauth_state(state)
        req_base_url = str(request.base_url).rstrip("/")
        url = build_authorize_url(state, base_url=req_base_url)
    except RuntimeError as e:
        msg = str(e)
        if "JWT_SECRET" in msg:
            raise HTTPException(status_code=500, detail="jwt_secret_missing")
        raise HTTPException(status_code=501, detail="oauth_not_configured")
    except Exception:
        raise HTTPException(status_code=500, detail="oauth_init_failed")
    return {"authorize_url": url}


async def github_callback(code: str, state: str) -> RedirectResponse:
    try:
        if not await consume_oauth_state(state):
            raise HTTPException(status_code=400, detail="invalid_state")
        token = await exchange_code(code)
        gh_user = await fetch_user(token)
        gh_id = int(gh_user.get("id"))
        login_hint = str(gh_user.get("login") or "github")
        u = await upsert_github_user(gh_id, login_hint)
        tokens = await issue_tokens(str(u["_id"]), str(u.get("login", "")))
    except HTTPException:
        raise
    except RuntimeError as e:
        msg = str(e)
        if "JWT_SECRET" in msg:
            raise HTTPException(status_code=500, detail="jwt_secret_missing")
        raise HTTPException(status_code=501, detail="oauth_not_configured")
    except Exception:
        raise HTTPException(status_code=500, detail="oauth_callback_failed")
    qs = urlencode({"access_token": tokens.access_token, "refresh_token": tokens.refresh_token})
    return RedirectResponse(url=f"/chat?{qs}", status_code=302)

