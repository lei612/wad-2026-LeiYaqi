from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from db import get_db, utc_now_iso


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as e:
        raise KeyError("invalid_id") from e


@dataclass(frozen=True)
class DocumentRow:
    id: str
    title: str
    current_version_id: str
    current_version_revision: int
    created_at: str


@dataclass(frozen=True)
class VersionRow:
    id: str
    document_id: str
    revision: int
    created_at: str


def list_documents() -> list[DocumentRow]:
    db = get_db()
    docs = list(db["documents"].find({}, sort=[("created_at", -1)]))
    out: list[DocumentRow] = []
    for d in docs:
        out.append(
            DocumentRow(
                id=str(d["_id"]),
                title=str(d.get("title", "Untitled")),
                current_version_id=str(d.get("current_version_id") or ""),
                current_version_revision=int(d.get("current_version_revision") or 0),
                created_at=str(d.get("created_at") or ""),
            )
        )
    return out


def create_document(title: str) -> DocumentRow:
    db = get_db()
    created_at = utc_now_iso()
    doc = {
        "title": title,
        "current_version_id": None,
        "current_version_revision": 0,
        "created_at": created_at,
    }
    res = db["documents"].insert_one(doc)
    return DocumentRow(
        id=str(res.inserted_id),
        title=title,
        current_version_id="",
        current_version_revision=0,
        created_at=created_at,
    )


def get_document(document_id: str) -> DocumentRow | None:
    db = get_db()
    d = db["documents"].find_one({"_id": _oid(document_id)})
    if d is None:
        return None
    return DocumentRow(
        id=str(d["_id"]),
        title=str(d.get("title", "Untitled")),
        current_version_id=str(d.get("current_version_id") or ""),
        current_version_revision=int(d.get("current_version_revision") or 0),
        created_at=str(d.get("created_at") or ""),
    )


def list_versions(document_id: str) -> list[VersionRow]:
    db = get_db()
    doc_oid = _oid(document_id)
    versions = list(db["document_versions"].find({"document_id": doc_oid}, sort=[("revision", -1)]))
    return [
        VersionRow(
            id=str(v["_id"]),
            document_id=document_id,
            revision=int(v.get("revision") or 0),
            created_at=str(v.get("created_at") or ""),
        )
        for v in versions
    ]


def get_version_content(document_id: str, version_id: str) -> dict[str, Any] | None:
    db = get_db()
    doc_oid = _oid(document_id)
    v = db["document_versions"].find_one({"_id": _oid(version_id), "document_id": doc_oid})
    if v is None:
        return None
    content = v.get("content")
    if isinstance(content, dict):
        return content
    return {"time": 0, "blocks": [], "version": "2"}


def get_current_content(document: DocumentRow) -> dict[str, Any]:
    if not document.current_version_id:
        return {"time": 0, "blocks": [], "version": "2"}
    content = get_version_content(document.id, document.current_version_id)
    if content is None:
        return {"time": 0, "blocks": [], "version": "2"}
    return content


def create_version(document_id: str, content: dict[str, Any]) -> tuple[str, int]:
    db = get_db()
    doc_oid = _oid(document_id)
    d = db["documents"].find_one({"_id": doc_oid})
    if d is None:
        raise KeyError("document_not_found")

    max_row = db["document_versions"].find_one(
        {"document_id": doc_oid},
        sort=[("revision", -1)],
        projection={"revision": 1},
    )
    next_rev = int(max_row.get("revision") or 0) + 1 if max_row else 1

    created_at = utc_now_iso()
    vdoc = {
        "document_id": doc_oid,
        "revision": next_rev,
        "content": content,
        "created_at": created_at,
    }
    vres = db["document_versions"].insert_one(vdoc)

    db["documents"].update_one(
        {"_id": doc_oid},
        {"$set": {"current_version_id": vres.inserted_id, "current_version_revision": next_rev}},
    )
    return str(vres.inserted_id), next_rev


def rollback_to_version(document_id: str, version_id: str) -> None:
    db = get_db()
    doc_oid = _oid(document_id)
    v = db["document_versions"].find_one({"_id": _oid(version_id), "document_id": doc_oid})
    if v is None:
        raise KeyError("version_not_found")
    revision = int(v.get("revision") or 0)
    db["documents"].update_one(
        {"_id": doc_oid},
        {"$set": {"current_version_id": v["_id"], "current_version_revision": revision}},
    )


def delete_document(document_id: str) -> None:
    db = get_db()
    doc_oid = _oid(document_id)
    res = db["documents"].delete_one({"_id": doc_oid})
    if res.deleted_count == 0:
        raise KeyError("document_not_found")
    db["document_versions"].delete_many({"document_id": doc_oid})


def delete_version(document_id: str, version_id: str) -> str:
    db = get_db()
    doc_oid = _oid(document_id)
    doc = db["documents"].find_one({"_id": doc_oid})
    if doc is None:
        raise KeyError("document_not_found")

    count = db["document_versions"].count_documents({"document_id": doc_oid})
    if count <= 1:
        raise ValueError("cannot_delete_last_version")

    v_oid = _oid(version_id)
    v = db["document_versions"].find_one({"_id": v_oid, "document_id": doc_oid})
    if v is None:
        raise KeyError("version_not_found")

    db["document_versions"].delete_one({"_id": v_oid, "document_id": doc_oid})

    current_id = doc.get("current_version_id")
    if current_id == v_oid:
        latest = db["document_versions"].find_one({"document_id": doc_oid}, sort=[("revision", -1)])
        if latest is None:
            raise ValueError("cannot_delete_last_version")
        db["documents"].update_one(
            {"_id": doc_oid},
            {"$set": {"current_version_id": latest["_id"], "current_version_revision": int(latest.get("revision") or 0)}},
        )
        return str(latest["_id"])

    return str(current_id or "")

