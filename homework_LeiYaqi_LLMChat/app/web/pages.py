from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> Any:
    resp = templates.TemplateResponse(request, "index.html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@router.get("/chat", response_class=HTMLResponse)
def chat(request: Request) -> Any:
    resp = templates.TemplateResponse(request, "chat.html")
    resp.headers["Cache-Control"] = "no-store"
    return resp
