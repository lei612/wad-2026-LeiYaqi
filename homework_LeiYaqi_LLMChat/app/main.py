from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.auth import oauth_router, router as auth_router
from .api.chats import router as chats_router
from .api.llm import router as llm_router
from .db import init_db
from .web.pages import router as pages_router


app = FastAPI(title="Homework 2 — LLM Chat (MVP)")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(chats_router)
app.include_router(llm_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
