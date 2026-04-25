from __future__ import annotations

from typing import Any

import httpx
from urllib.parse import urlencode

from ..settings import get_settings


GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def build_authorize_url(state: str, *, base_url: str | None = None) -> str:
    s = get_settings()
    if not s.github_client_id:
        raise RuntimeError("GITHUB_CLIENT_ID is not set")
    effective_base = (base_url or s.base_url).rstrip("/")
    redirect_uri = f"{effective_base}/auth/github/callback"
    qs = urlencode(
        {
            "client_id": s.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
    )
    return f"{GITHUB_AUTHORIZE_URL}?{qs}"


def exchange_code(code: str) -> str:
    s = get_settings()
    if not s.github_client_id or not s.github_client_secret:
        raise RuntimeError("GitHub OAuth is not configured")

    with httpx.Client(timeout=10, follow_redirects=True, trust_env=False) as c:
        r = c.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": s.github_client_id,
                "client_secret": s.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("oauth_exchange_failed")
        return str(token)


def fetch_user(access_token: str) -> dict[str, Any]:
    with httpx.Client(timeout=10, trust_env=False) as c:
        r = c.get(GITHUB_USER_URL, headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"})
        r.raise_for_status()
        return r.json()
