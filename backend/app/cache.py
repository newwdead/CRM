"""
Redis caching utilities
"""
import redis
import hashlib
import pickle
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = None

try:
    redis_client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=False,  # We'll use pickle for serialization
        socket_connect_timeout=5,
        socket_timeout=5
    )
    redis_client.ping()
    logger.info(f"Redis connected: {REDIS_URL}")
except Exception as e:
    logger.warning(f"Redis unavailable: {e}. Caching disabled.")
    redis_client = None


def get_cache_key(prefix: str, data: bytes, extra: str = "") -> str:
    """
    Generate a cache key from image bytes and extra parameters.
    
    Args:
        prefix: Cache key prefix (e.g., 'ocr', 'qr')
        data: Image bytes to hash
        extra: Extra parameters to include in key (e.g., provider name)
    
    Returns:
        Cache key string
    """
    # Using MD5 for cache key generation only (not for security)
    hash_value = hashlib.md5(data, usedforsecurity=False).hexdigest()  # nosec B324
    if extra:
        return f"{prefix}:{extra}:{hash_value}"
    return f"{prefix}:{hash_value}"


def get_from_cache(key: str):
    """
    Get value from Redis cache.
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found/unavailable
    """
    if not redis_client:
        return None
    
    try:
        cached = redis_client.get(key)
        if cached:
            logger.info(f"Cache HIT: {key[:50]}...")
            # Using pickle for internal cache only (trusted data)
            # For untrusted data, use JSON serialization instead
            return pickle.loads(cached)  # nosec B301
        logger.debug(f"Cache MISS: {key[:50]}...")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def set_to_cache(key: str, value, ttl: int = 86400):
    """
    Set value to Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache (will be pickled)
        ttl: Time to live in seconds (default: 24 hours)
    """
    if not redis_client:
        return False
    
    try:
        serialized = pickle.dumps(value)
        redis_client.setex(key, ttl, serialized)
        logger.debug(f"Cache SET: {key[:50]}... (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


def delete_from_cache(key: str):
    """
    Delete value from Redis cache.
    
    Args:
        key: Cache key
    """
    if not redis_client:
        return False
    
    try:
        redis_client.delete(key)
        logger.debug(f"Cache DELETE: {key[:50]}...")
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


def clear_cache(pattern: str = "*"):
    """
    Clear all keys matching pattern.
    
    Args:
        pattern: Redis key pattern (default: all keys)
    
    Warning:
        Use with caution! This will delete all matching keys.
    """
    if not redis_client:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cache cleared: {len(keys)} keys matching '{pattern}'")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return 0


def get_cache_stats() -> dict:
    """
    Get Redis cache statistics.
    
    Returns:
        Dictionary with cache stats (or empty dict if unavailable)
    """
    if not redis_client:
        return {"available": False}
    
    try:
        info = redis_client.info()
        return {
            "available": True,
            "used_memory": info.get("used_memory_human", "N/A"),
            "connected_clients": info.get("connected_clients", 0),
            "total_keys": redis_client.dbsize(),
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"available": False, "error": str(e)}

