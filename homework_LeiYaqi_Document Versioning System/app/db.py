from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def _build_client() -> Any:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    if uri.startswith("mongomock://"):
        import mongomock

        return mongomock.MongoClient()
    return MongoClient(uri, serverSelectionTimeoutMS=2000)


@lru_cache(maxsize=1)
def get_db() -> Any:
    client = _build_client()
    db_name = os.getenv("MONGODB_DB", "doc_versioning")
    return client[db_name]


def init_db() -> None:
    db = get_db()
    db["document_versions"].create_index(
        [("document_id", ASCENDING), ("revision", ASCENDING)],
        unique=True,
        name="idx_document_versions_doc_revision",
    )
    db["document_versions"].create_index(
        [("document_id", ASCENDING), ("created_at", DESCENDING)],
        name="idx_document_versions_doc_created",
    )
    db["documents"].create_index(
        [("created_at", DESCENDING)],
        name="idx_documents_created",
    )

