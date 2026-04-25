from __future__ import annotations

from typing import Any

from bson import ObjectId

from ..db import get_db
from ..security import hash_password, verify_password


def _id_str(doc: dict[str, Any]) -> str:
    return str(doc["_id"])


def create_user(login: str, password: str) -> dict[str, Any]:
    db = get_db()
    doc = {"login": login, "password_hash": hash_password(password)}
    res = db["users"].insert_one(doc)
    return {"id": str(res.inserted_id), "login": login}


def get_user_by_login(login: str) -> dict[str, Any] | None:
    db = get_db()
    u = db["users"].find_one({"login": login})
    return u


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    return db["users"].find_one({"_id": oid})


def verify_user_password(user: dict[str, Any], password: str) -> bool:
    return verify_password(password, str(user.get("password_hash", "")))


def set_user_password(user_id: str, password: str) -> bool:
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        return False
    res = db["users"].update_one({"_id": oid}, {"$set": {"password_hash": hash_password(password)}})
    return bool(res.modified_count)


def upsert_github_user(github_id: int, login_hint: str) -> dict[str, Any]:
    db = get_db()
    existing = db["users"].find_one({"github_id": github_id})
    if existing is not None:
        return existing

    base = login_hint[:48] or "github"
    candidate = base
    i = 0
    while db["users"].find_one({"login": candidate}) is not None:
        i += 1
        candidate = f"{base}{i}"

    doc = {"login": candidate, "github_id": github_id, "password_hash": ""}
    res = db["users"].insert_one(doc)
    return {"_id": res.inserted_id, "login": candidate, "github_id": github_id}
