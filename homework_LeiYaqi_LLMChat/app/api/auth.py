from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..settings import get_settings
from ..schemas import LoginIn, RefreshIn, RegisterIn, TokensOut, UserOut
from ..services.auth import consume_oauth_state, issue_tokens, new_oauth_state, refresh_access_token, store_oauth_state
from ..services.oauth_github import build_authorize_url, exchange_code, fetch_user
from ..services.users import create_user, get_user_by_login, set_user_password, upsert_github_user, verify_user_password


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn) -> UserOut:
    existing = get_user_by_login(payload.login)
    if existing is not None:
        if existing.get("github_id") is not None and not str(existing.get("password_hash") or "").strip():
            ok = set_user_password(str(existing["_id"]), payload.password)
            if not ok:
                raise HTTPException(status_code=500, detail="password_set_failed")
            return UserOut(id=str(existing["_id"]), login=str(existing.get("login", "")))
        raise HTTPException(status_code=409, detail="login_taken")
    u = create_user(payload.login, payload.password)
    created = get_user_by_login(payload.login)
    if created is None:
        raise HTTPException(status_code=500, detail="user_create_failed")
    if not verify_user_password(created, payload.password):
        raise HTTPException(status_code=500, detail="password_hash_failed")
    return UserOut(id=u["id"], login=u["login"])


@router.post("/login", response_model=TokensOut)
def login(payload: LoginIn) -> TokensOut:
    u = get_user_by_login(payload.login)
    if u is None:
        raise HTTPException(status_code=401, detail="user_not_found")
    if not verify_user_password(u, payload.password):
        raise HTTPException(status_code=401, detail="wrong_password")
    tokens = issue_tokens(str(u["_id"]), str(u.get("login", "")))
    return TokensOut(access_token=tokens.access_token, refresh_token=tokens.refresh_token, token_type=tokens.token_type)


@router.post("/refresh")
def refresh(payload: RefreshIn) -> dict[str, str]:
    try:
        access = refresh_access_token(payload.refresh_token)
    except KeyError:
        raise HTTPException(status_code=401, detail="invalid_refresh")
    return {"access_token": access, "token_type": "bearer"}


oauth_router = APIRouter(tags=["oauth"])


@oauth_router.get("/auth/github/status")
def github_status(request: Request) -> dict[str, object]:
    s = get_settings()
    return {
        "has_jwt_secret": bool(str(s.jwt_secret or "").strip()),
        "has_github_client_id": bool(s.github_client_id),
        "has_github_client_secret": bool(s.github_client_secret),
        "request_base_url": str(request.base_url).rstrip("/"),
        "settings_base_url": str(s.base_url).rstrip("/"),
    }


@oauth_router.get("/auth/github/login")
def github_login(request: Request) -> dict[str, str]:
    try:
        state = new_oauth_state()
        store_oauth_state(state)
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


@oauth_router.get("/auth/github/callback")
def github_callback(code: str, state: str):
    try:
        if not consume_oauth_state(state):
            raise HTTPException(status_code=400, detail="invalid_state")
        token = exchange_code(code)
        gh_user = fetch_user(token)
        gh_id = int(gh_user.get("id"))
        login_hint = str(gh_user.get("login") or "github")
        u = upsert_github_user(gh_id, login_hint)
        tokens = issue_tokens(str(u["_id"]), str(u.get("login", "")))
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
