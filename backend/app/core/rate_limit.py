"""Global rate limiting for LLM calls and API endpoints."""

import logging
import time
import threading
from collections import defaultdict

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global daily LLM rate limiter (200 requests/day across ALL users)
# ---------------------------------------------------------------------------

_llm_lock = threading.Lock()
_llm_daily_count: int = 0
_llm_daily_reset_time: float = time.time() + 86400  # 24h from startup


def check_llm_daily_limit() -> int:
    """Check and increment the global LLM daily counter.

    Returns the number of remaining requests.
    Raises HTTPException(429) if the daily limit is exceeded.
    """
    global _llm_daily_count, _llm_daily_reset_time

    with _llm_lock:
        now = time.time()
        if now >= _llm_daily_reset_time:
            _llm_daily_count = 0
            _llm_daily_reset_time = now + 86400
            logger.info("LLM daily counter reset")

        if _llm_daily_count >= 200:
            raise HTTPException(
                status_code=429,
                detail="Daily AI quota reached (200/day). Please try again tomorrow.",
            )

        _llm_daily_count += 1
        remaining = 200 - _llm_daily_count
        logger.info("LLM request %d/200 (remaining: %d)", _llm_daily_count, remaining)
        return remaining


def get_llm_usage() -> dict:
    """Return current LLM usage stats (for admin dashboard)."""
    global _llm_daily_count, _llm_daily_reset_time
    with _llm_lock:
        return {
            "used": _llm_daily_count,
            "limit": 200,
            "remaining": max(0, 200 - _llm_daily_count),
            "resets_at": _llm_daily_reset_time,
        }


# ---------------------------------------------------------------------------
# Per-IP rate limiter (general purpose, in-memory)
# ---------------------------------------------------------------------------

_ip_lock = threading.Lock()
_ip_requests: dict[str, list[float]] = defaultdict(list)


def check_ip_rate_limit(
    request: Request,
    max_requests: int = 60,
    window_seconds: int = 60,
    endpoint_tag: str = "api",
) -> None:
    """Per-IP rate limiting. Raises HTTPException(429) if exceeded."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"{endpoint_tag}:{client_ip}"

    with _ip_lock:
        now = time.time()
        _ip_requests[key] = [t for t in _ip_requests[key] if now - t < window_seconds]

        if len(_ip_requests[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({max_requests} requests per {window_seconds}s). Please slow down.",
            )

        _ip_requests[key].append(now)
