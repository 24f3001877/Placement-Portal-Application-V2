# RecruitRadar — cache.py
# Redis caching helpers. All keys use the "rr_cache" prefix.
# Import redis_client from extensions after app initialization.

import json
import functools
from flask import current_app


def _get_client():
    """Return the Redis client from extensions (initialized in app.py)."""
    from extensions import redis_client
    return redis_client


def rr_cache_get(key: str):
    """
    Retrieve a value from Redis cache.
    Keys are always prefixed with 'rr_cache:' to namespace RecruitRadar data.
    Returns the parsed Python object or None if not found / Redis unavailable.
    """
    try:
        client = _get_client()
        if client is None:
            return None
        full_key = f"rr_cache:{key}"
        raw = client.get(full_key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        # If Redis is unavailable, degrade gracefully — don't crash the request
        return None


def rr_cache_set(key: str, value, ttl: int = 120) -> None:
    """
    Store a value in Redis cache with a TTL in seconds.
    Default TTL is 2 minutes (120 seconds).
    """
    try:
        client = _get_client()
        if client is None:
            return
        full_key = f"rr_cache:{key}"
        client.setex(full_key, ttl, json.dumps(value))
    except Exception:
        pass  # Degrade gracefully if Redis is unavailable


def rr_cache_delete(key: str) -> None:
    """Delete a specific key from the cache (call on write operations)."""
    try:
        client = _get_client()
        if client is None:
            return
        full_key = f"rr_cache:{key}"
        client.delete(full_key)
    except Exception:
        pass


def rr_cache_delete_pattern(pattern: str) -> None:
    """
    Delete all keys matching a pattern (e.g. 'rr_cache:drives:*').
    Used to invalidate related cache entries after a write.
    """
    try:
        client = _get_client()
        if client is None:
            return
        full_pattern = f"rr_cache:{pattern}"
        keys = client.keys(full_pattern)
        if keys:
            client.delete(*keys)
    except Exception:
        pass


def rr_cached(key_fn, ttl_config_key: str = "RR_CACHE_TTL_DRIVES"):
    """
    Decorator factory for caching route responses.
    key_fn: a callable that returns the cache key string.
    ttl_config_key: the config variable name for TTL.

    Usage:
        @rr_cached(lambda: "admin:dashboard", "RR_CACHE_TTL_DASHBOARD")
        def get_dashboard(): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key_fn(*args, **kwargs) if callable(key_fn) else key_fn
            ttl = current_app.config.get(ttl_config_key, 120)

            cached = rr_cache_get(cache_key)
            if cached is not None:
                return cached  # Return cached dict directly

            result = func(*args, **kwargs)
            rr_cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
