from __future__ import annotations

from functools import lru_cache
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from .settings import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> Any:
    s = get_settings()
    if s.mongo_uri.startswith("mongomock://"):
        from mongomock_motor import AsyncMongoMockClient

        return AsyncMongoMockClient()
    return AsyncIOMotorClient(s.mongo_uri, serverSelectionTimeoutMS=2000)


def get_db() -> Any:
    s = get_settings()
    client = get_mongo_client()
    return client[s.mongo_db]


def close_db() -> None:
    client = get_mongo_client()
    close = getattr(client, "close", None)
    if callable(close):
        close()


async def init_db() -> None:
    db = get_db()
    await db["users"].create_index([("login", 1)], unique=True, name="idx_users_login")
    await db["users"].create_index([("github_id", 1)], unique=True, sparse=True, name="idx_users_github_id")

    await db["chats"].create_index([("user_id", 1), ("created_at", -1)], name="idx_chats_user_created")
    await db["messages"].create_index([("chat_id", 1), ("created_at", 1)], name="idx_messages_chat_created")
