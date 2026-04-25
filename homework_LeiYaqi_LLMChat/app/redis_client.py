from __future__ import annotations

from functools import lru_cache

import redis

from .settings import get_settings


@lru_cache(maxsize=1)
def get_redis() -> redis.Redis:
    s = get_settings()
    if s.redis_url.startswith("fakeredis://"):
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True)
    return redis.from_url(s.redis_url, decode_responses=True)
