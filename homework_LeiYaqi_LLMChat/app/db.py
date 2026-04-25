from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient

from .settings import get_settings


@lru_cache(maxsize=1)
def get_db() -> Any:
    s = get_settings()
    if s.mongo_uri.startswith("mongomock://"):
        import mongomock

        client = mongomock.MongoClient()
    else:
        client = MongoClient(s.mongo_uri, serverSelectionTimeoutMS=2000)
    return client[s.mongo_db]


def init_db() -> None:
    db = get_db()
    db["users"].create_index([("login", ASCENDING)], unique=True, name="idx_users_login")
    db["users"].create_index([("github_id", ASCENDING)], unique=True, sparse=True, name="idx_users_github_id")

    db["chats"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_chats_user_created")
    db["messages"].create_index([("chat_id", ASCENDING), ("created_at", ASCENDING)], name="idx_messages_chat_created")
