from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import init_db
from schemas import (
    DocumentCreate,
    DocumentOut,
    DocumentWithContent,
    VersionCreate,
    VersionOut,
)
from storage import (
    create_document,
    create_version,
    delete_document,
    delete_version,
    get_current_content,
    get_document,
    get_version_content,
    list_documents,
    list_versions,
    rollback_to_version,
)


app = FastAPI(title="Document Versioning System (MVP)")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def ui(request: Request) -> Any:
    return templates.TemplateResponse(request, "editor.html")


@app.get("/api/documents", response_model=list[DocumentOut])
def api_list_documents() -> list[DocumentOut]:
    return [DocumentOut(**d.__dict__) for d in list_documents()]


@app.post("/api/documents", response_model=DocumentOut)
def api_create_document(payload: DocumentCreate) -> DocumentOut:
    doc = create_document(title=payload.title)
    return DocumentOut(**doc.__dict__)


@app.delete("/api/documents/{document_id}")
def api_delete_document(document_id: str) -> dict[str, str]:
    try:
        delete_document(document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="document_not_found")
    return {"status": "ok"}


@app.get("/api/documents/{document_id}", response_model=DocumentWithContent)
def api_get_document(document_id: str) -> DocumentWithContent:
    try:
        doc = get_document(document_id)
    except KeyError:
        raise HTTPException(status_code=422, detail="invalid_id")
    if doc is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    content = get_current_content(doc)
    return DocumentWithContent(**doc.__dict__, content=content)


@app.get("/api/documents/{document_id}/versions", response_model=list[VersionOut])
def api_list_versions(document_id: str) -> list[VersionOut]:
    doc = get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    return [VersionOut(**v.__dict__) for v in list_versions(document_id)]


@app.get("/api/documents/{document_id}/versions/{version_id}")
def api_get_version(document_id: str, version_id: str) -> dict[str, Any]:
    content = get_version_content(document_id, version_id)
    if content is None:
        raise HTTPException(status_code=404, detail="version_not_found")
    return content


@app.delete("/api/documents/{document_id}/versions/{version_id}")
def api_delete_version(document_id: str, version_id: str) -> dict[str, str]:
    try:
        new_current = delete_version(document_id=document_id, version_id=version_id)
    except KeyError as e:
        detail = str(e).strip("'")
        if detail not in {"document_not_found", "version_not_found"}:
            detail = "not_found"
        raise HTTPException(status_code=404, detail=detail)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "ok", "current_version_id": new_current}


@app.post("/api/documents/{document_id}/versions")
def api_create_version(document_id: str, payload: VersionCreate) -> dict[str, int | str]:
    # Editor.js data is stored as an immutable JSON snapshot per version.
    blocks = payload.content.get("blocks")
    if not isinstance(blocks, list):
        raise HTTPException(status_code=422, detail="invalid_editorjs_content")
    try:
        version_id, revision = create_version(document_id=document_id, content=payload.content)
    except KeyError:
        raise HTTPException(status_code=404, detail="document_not_found")
    return {"version_id": version_id, "revision": revision}


@app.post("/api/documents/{document_id}/rollback/{version_id}")
def api_rollback(document_id: str, version_id: str) -> dict[str, str]:
    try:
        rollback_to_version(document_id=document_id, version_id=version_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="version_not_found")
    return {"status": "ok"}

