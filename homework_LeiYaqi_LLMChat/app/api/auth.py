from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..schemas import LoginIn, RefreshIn, RegisterIn, TokensOut, UserOut
from ..services import auth_usecases


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: RegisterIn) -> UserOut:
    return await auth_usecases.register(payload)


@router.post("/login", response_model=TokensOut)
async def login(payload: LoginIn) -> TokensOut:
    return await auth_usecases.login(payload)


@router.post("/refresh")
async def refresh(payload: RefreshIn) -> dict[str, str]:
    return await auth_usecases.refresh(payload)


oauth_router = APIRouter(tags=["oauth"])


@oauth_router.get("/auth/github/status")
def github_status(request: Request) -> dict[str, object]:
    return auth_usecases.github_status(request)


@oauth_router.get("/auth/github/login")
async def github_login(request: Request) -> dict[str, str]:
    return await auth_usecases.github_login(request)


@oauth_router.get("/auth/github/callback")
async def github_callback(code: str, state: str) -> RedirectResponse:
    return await auth_usecases.github_callback(code, state)
