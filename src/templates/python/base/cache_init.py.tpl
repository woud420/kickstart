"""Cache infrastructure components.

This module provides Redis-based caching functionality with
connection management, serialization, and common operations.
"""

{% block imports %}
from .redis_cache import (
    RedisCache,
    CacheError,
    SerializationError,
    create_redis_client,
    get_redis_client,
    close_redis_client,
    get_cache_health,
    get_cache,
    cached
)
{% endblock %}

{% block exports %}
__all__ = [
    "RedisCache",
    "CacheError",
    "SerializationError",
    "create_redis_client",
    "get_redis_client",
    "close_redis_client",
    "get_cache_health",
    "get_cache",
    "cached",
]
{% endblock %}