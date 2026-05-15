import os
import time

import httpx


def main() -> None:
    base = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    with httpx.Client(timeout=240, trust_env=False) as c:
        login = f"user{int(time.time())}"
        password = "password123"

        r = c.post(f"{base}/api/auth/register", json={"login": login, "password": password})
        r.raise_for_status()

        r = c.post(f"{base}/api/auth/login", json={"login": login, "password": password})
        r.raise_for_status()
        tokens = r.json()
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        r = c.post(f"{base}/api/chats", json={"title": "Test chat"}, headers={"Authorization": f"Bearer {access}"})
        r.raise_for_status()
        chat_id = r.json()["id"]

        r = c.post(
            f"{base}/api/chats/{chat_id}/messages",
            json={"content": "Hello"},
            headers={"Authorization": f"Bearer {access}"},
        )
        r.raise_for_status()

        r = c.post(f"{base}/api/auth/refresh", json={"refresh_token": refresh})
        r.raise_for_status()
        new_access = r.json()["access_token"]

        r = c.get(f"{base}/api/chats/{chat_id}", headers={"Authorization": f"Bearer {new_access}"})
        r.raise_for_status()
        data = r.json()
        assert len(data["messages"]) >= 2

    print("OK")


if __name__ == "__main__":
    main()
