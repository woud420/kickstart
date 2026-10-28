"""Redis cache implementation.

This module provides Redis-based caching functionality with
connection management, serialization, and common cache operations.
"""

import redis.asyncio as redis
import json
import pickle
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
from functools import lru_cache

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class SerializationError(CacheError):
    """Raised when serialization/deserialization fails."""
    pass


class CacheSerializer:
    """Handles serialization/deserialization for cache operations."""
    
    @staticmethod
    def serialize(value: Any, use_pickle: bool = False) -> bytes:
        """Serialize a value for storage in cache.
        
        Args:
            value: Value to serialize
            use_pickle: Whether to use pickle for complex objects
            
        Returns:
            Serialized value as bytes
            
        Raises:
            SerializationError: If serialization fails
        """
        try:
            if use_pickle:
                return pickle.dumps(value)
            else:
                # Try JSON first for better compatibility
                if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                    return json.dumps(value).encode('utf-8')
                else:
                    # Fall back to pickle for complex objects
                    return pickle.dumps(value)
        except Exception as e:
            raise SerializationError(f"Failed to serialize value: {e}") from e
    
    @staticmethod
    def deserialize(data: bytes, use_pickle: bool = False) -> Any:
        """Deserialize a value from cache storage.
        
        Args:
            data: Serialized data from cache
            use_pickle: Whether to use pickle for deserialization
            
        Returns:
            Deserialized value
            
        Raises:
            SerializationError: If deserialization fails
        """
        try:
            if use_pickle:
                return pickle.loads(data)
            else:
                # Try JSON first
                try:
                    return json.loads(data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fall back to pickle
                    return pickle.loads(data)
        except Exception as e:
            raise SerializationError(f"Failed to deserialize value: {e}") from e


async def create_redis_client() -> redis.Redis:
    """Create and configure Redis client.
    
    Returns:
        Configured Redis client
        
    Raises:
        CacheError: If unable to connect to Redis
    """
    try:
        settings = get_settings()
        
        # Redis connection parameters
        connection_kwargs = {
            "host": settings.redis_host,
            "port": settings.redis_port,
            "password": settings.redis_password if settings.redis_password else None,
            "db": settings.redis_db,
            "decode_responses": False,  # We handle serialization manually
            "max_connections": settings.redis_pool_max_connections,
            "retry_on_timeout": True,
            "socket_connect_timeout": settings.redis_socket_timeout,
            "socket_timeout": settings.redis_socket_timeout,
        }
        
        # Add SSL config if specified
        if settings.redis_ssl:
            connection_kwargs["ssl"] = True
            connection_kwargs["ssl_cert_reqs"] = "required"
        
        logger.info(f"Creating Redis client: {settings.redis_host}:{settings.redis_port}")
        
        client = redis.Redis(**connection_kwargs)
        
        # Test the connection
        await client.ping()
        
        logger.info("Redis client created successfully")
        return client
        
    except redis.RedisError as e:
        logger.error(f"Redis error creating client: {e}")
        raise CacheError(f"Redis connection failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error creating Redis client: {e}")
        raise CacheError(f"Cache client setup failed: {e}") from e


@lru_cache()
async def get_redis_client() -> redis.Redis:
    """Get or create the global Redis client.
    
    Returns:
        Redis client
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await create_redis_client()
    
    return _redis_client


async def close_redis_client() -> None:
    """Close the global Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        logger.info("Closing Redis client")
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis client closed")


class RedisCache:
    """Redis cache implementation with common operations."""
    
    def __init__(self, client: Optional[redis.Redis] = None, key_prefix: str = ""):
        """Initialize Redis cache.
        
        Args:
            client: Redis client (will create one if not provided)
            key_prefix: Prefix for all cache keys
        """
        self.client = client
        self.key_prefix = key_prefix
        self.serializer = CacheSerializer()
    
    async def _get_client(self) -> redis.Redis:
        """Get Redis client, creating one if necessary."""
        if self.client is None:
            self.client = await get_redis_client()
        return self.client
    
    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix.
        
        Args:
            key: Base key name
            
        Returns:
            Full cache key
        """
        if self.key_prefix:
            return f"{self.key_prefix}:{key}"
        return key
    
    async def get(self, key: str, default: Any = None, use_pickle: bool = False) -> Any:
        """Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            use_pickle: Whether to use pickle for deserialization
            
        Returns:
            Cached value or default
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            data = await client.get(full_key)
            if data is None:
                return default
            
            return self.serializer.deserialize(data, use_pickle)
            
        except Exception as e:
            logger.warning(f"Failed to get cache key '{key}': {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        use_pickle: bool = False
    ) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live (seconds or timedelta)
            use_pickle: Whether to use pickle for serialization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            serialized_data = self.serializer.serialize(value, use_pickle)
            
            if ttl is not None:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                return await client.setex(full_key, ttl, serialized_data)
            else:
                return await client.set(full_key, serialized_data)
            
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            result = await client.delete(full_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            result = await client.exists(full_key)
            return result > 0
            
        except Exception as e:
            logger.warning(f"Failed to check cache key '{key}': {e}")
            return False
    
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time to live (seconds or timedelta)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            return await client.expire(full_key, ttl)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key '{key}': {e}")
            return False
    
    async def get_many(self, keys: List[str], use_pickle: bool = False) -> Dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            use_pickle: Whether to use pickle for deserialization
            
        Returns:
            Dictionary of key-value pairs
        """
        try:
            client = await self._get_client()
            full_keys = [self._make_key(key) for key in keys]
            
            values = await client.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self.serializer.deserialize(value, use_pickle)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get multiple cache keys: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None,
        use_pickle: bool = False
    ) -> bool:
        """Set multiple values in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live for all keys
            use_pickle: Whether to use pickle for serialization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            
            # Prepare data
            cache_data = {}
            for key, value in mapping.items():
                full_key = self._make_key(key)
                serialized_data = self.serializer.serialize(value, use_pickle)
                cache_data[full_key] = serialized_data
            
            # Set all values
            await client.mset(cache_data)
            
            # Set TTL if specified
            if ttl is not None:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                
                # Set expiration for all keys
                for full_key in cache_data.keys():
                    await client.expire(full_key, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set multiple cache keys: {e}")
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values from cache.
        
        Args:
            keys: List of cache keys to delete
            
        Returns:
            Number of keys actually deleted
        """
        try:
            client = await self._get_client()
            full_keys = [self._make_key(key) for key in keys]
            
            return await client.delete(*full_keys)
            
        except Exception as e:
            logger.error(f"Failed to delete multiple cache keys: {e}")
            return 0
    
    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        try:
            client = await self._get_client()
            full_pattern = self._make_key(pattern)
            
            keys = await client.keys(full_pattern)
            if keys:
                return await client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern '{pattern}': {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment, or None if failed
        """
        try:
            client = await self._get_client()
            full_key = self._make_key(key)
            
            return await client.incrby(full_key, amount)
            
        except Exception as e:
            logger.error(f"Failed to increment cache key '{key}': {e}")
            return None


async def get_cache_health() -> Dict[str, Any]:
    """Check Redis cache health and return status information.
    
    Returns:
        Cache health information
    """
    try:
        import time
        
        start_time = time.time()
        
        client = await get_redis_client()
        
        # Test basic connectivity
        ping_result = await client.ping()
        
        # Get Redis info
        info = await client.info()
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "healthy": True,
            "ping": ping_result,
            "response_time_ms": round(response_time_ms, 2),
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory": info.get("used_memory"),
            "used_memory_human": info.get("used_memory_human"),
            "keyspace": {
                key: value for key, value in info.items() 
                if key.startswith("db")
            }
        }
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# Create default cache instance
_default_cache: Optional[RedisCache] = None


async def get_cache(key_prefix: str = "") -> RedisCache:
    """Get a cache instance.
    
    Args:
        key_prefix: Key prefix for this cache instance
        
    Returns:
        Redis cache instance
    """
    global _default_cache
    
    if _default_cache is None:
        client = await get_redis_client()
        _default_cache = RedisCache(client)
    
    if key_prefix:
        client = await get_redis_client()
        return RedisCache(client, key_prefix)
    
    return _default_cache


# Cache decorator
def cached(ttl: Union[int, timedelta] = 300, key_prefix: str = "", use_pickle: bool = False):
    """Decorator for caching function results.
    
    Args:
        ttl: Time to live for cached results
        key_prefix: Prefix for cache keys
        use_pickle: Whether to use pickle for serialization
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            import hashlib
            
            key_parts = [func.__name__]
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(tuple(sorted(kwargs.items())))))
            
            cache_key = ":".join(key_parts)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            
            # Try to get from cache
            cache = await get_cache()
            result = await cache.get(cache_key, use_pickle=use_pickle)
            
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            
            await cache.set(cache_key, result, ttl, use_pickle=use_pickle)
            
            return result
        
        return wrapper
    return decorator