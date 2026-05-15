from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class DocumentOut(BaseModel):
    id: str
    title: str
    current_version_id: str
    current_version_revision: int
    created_at: str


class DocumentWithContent(DocumentOut):
    content: dict[str, Any]


class VersionOut(BaseModel):
    id: str
    document_id: str
    revision: int
    created_at: str


class VersionCreate(BaseModel):
    content: dict[str, Any]

