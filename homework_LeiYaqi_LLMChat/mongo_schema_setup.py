import os

from pymongo import ASCENDING, DESCENDING, MongoClient


def main() -> None:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "wad_homework_2")
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    db = client[db_name]

    db["users"].create_index([("login", ASCENDING)], unique=True, name="idx_users_login")
    db["users"].create_index([("github_id", ASCENDING)], unique=True, sparse=True, name="idx_users_github_id")
    db["chats"].create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_chats_user_created")
    db["messages"].create_index([("chat_id", ASCENDING), ("created_at", ASCENDING)], name="idx_messages_chat_created")

    print("OK: MongoDB indexes created")


if __name__ == "__main__":
    main()

