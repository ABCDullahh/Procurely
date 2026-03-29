"""Redis client for caching and rate limiting."""
import json
import logging
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance. Returns None if Redis unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _redis_client.ping()
        logger.info("Redis connected")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}. Caching disabled.")
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    r = get_redis()
    if not r:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL (default 1 hour)."""
    r = get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False


def cache_delete(key: str) -> bool:
    """Delete a cache key."""
    r = get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except Exception:
        return False
