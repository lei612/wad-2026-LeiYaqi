from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from ..db import get_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_chat(user_id: str, title: str) -> dict[str, Any]:
    db = get_db()
    doc = {"user_id": ObjectId(user_id), "title": title, "created_at": _now_iso()}
    res = db["chats"].insert_one(doc)
    return {"id": str(res.inserted_id), "title": title, "created_at": doc["created_at"]}


def list_chats(user_id: str) -> list[dict[str, Any]]:
    db = get_db()
    uid = ObjectId(user_id)
    chats = list(db["chats"].find({"user_id": uid}, sort=[("created_at", -1)]))
    return [{"id": str(c["_id"]), "title": str(c.get("title", "")), "created_at": str(c.get("created_at", ""))} for c in chats]


def get_chat(user_id: str, chat_id: str) -> dict[str, Any] | None:
    db = get_db()
    uid = ObjectId(user_id)
    cid = ObjectId(chat_id)
    return db["chats"].find_one({"_id": cid, "user_id": uid})


def list_messages(user_id: str, chat_id: str) -> list[dict[str, Any]]:
    db = get_db()
    cid = ObjectId(chat_id)
    msgs = list(db["messages"].find({"chat_id": cid}, sort=[("created_at", 1)]))
    out: list[dict[str, Any]] = []
    for m in msgs:
        out.append(
            {
                "id": str(m["_id"]),
                "role": str(m.get("role", "")),
                "content": str(m.get("content", "")),
                "created_at": str(m.get("created_at", "")),
            }
        )
    return out


def add_message(chat_id: str, user_id: str, role: str, content: str) -> dict[str, Any]:
    db = get_db()
    doc = {
        "chat_id": ObjectId(chat_id),
        "user_id": ObjectId(user_id),
        "role": role,
        "content": content,
        "created_at": _now_iso(),
    }
    res = db["messages"].insert_one(doc)
    return {"id": str(res.inserted_id), "role": role, "content": content, "created_at": doc["created_at"]}


def delete_chat(user_id: str, chat_id: str) -> bool:
    db = get_db()
    uid = ObjectId(user_id)
    cid = ObjectId(chat_id)
    res = db["chats"].delete_one({"_id": cid, "user_id": uid})
    if res.deleted_count:
        db["messages"].delete_many({"chat_id": cid})
        return True
    return False
