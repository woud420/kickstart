"""Infrastructure layer for external dependencies.

This module contains infrastructure components for databases,
caching, external services, and other system dependencies.
"""

{% block imports %}
from .database import *
from .cache import *
{% endblock %}

{% block exports %}
__all__ = [
    # Database
    "create_database_pool",
    "get_database_pool",
    "get_database_connection",
    "get_database_transaction",
    "get_database_health",
    "initialize_database",
    "shutdown_database",

    # Cache
    "RedisCache",
    "get_redis_client",
    "get_cache_health",
    "get_cache",
    "cached",
]
{% endblock %}