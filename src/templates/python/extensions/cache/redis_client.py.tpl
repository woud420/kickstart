"""Redis cache client for {{service_name}}.

This module provides Redis caching functionality as an extension to the core service.
"""

import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client with async support."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, 
                 password: Optional[str] = None, db: int = 0,
                 decode_responses: bool = True):
        """Initialize Redis cache client.
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password (optional)
            db: Redis database number
            decode_responses: Whether to decode responses to strings
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.decode_responses = decode_responses
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=self.decode_responses,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Redis."""
        return self._connected and self._client is not None
    
    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is active."""
        if not self.is_connected:
            await self.connect()
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire: Expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            await self._ensure_connected()
            
            # Serialize value to JSON
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            result = await self._client.set(key, serialized_value, ex=expire)
            logger.debug(f"Cache SET: {key} (expire: {expire}s)")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            await self._ensure_connected()
            
            value = await self._client.get(key)
            if value is None:
                logger.debug(f"Cache MISS: {key}")
                return None
            
            # Try to deserialize JSON
            try:
                result = json.loads(value)
                logger.debug(f"Cache HIT: {key}")
                return result
            except json.JSONDecodeError:
                # Return as string if not JSON
                logger.debug(f"Cache HIT (string): {key}")
                return value
            
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            await self._ensure_connected()
            
            result = await self._client.delete(key)
            deleted = bool(result)
            logger.debug(f"Cache DELETE: {key} (deleted: {deleted})")
            return deleted
            
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            await self._ensure_connected()
            
            result = await self._client.exists(key)
            exists = bool(result)
            logger.debug(f"Cache EXISTS: {key} = {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if expiration was set
        """
        try:
            await self._ensure_connected()
            
            result = await self._client.expire(key, seconds)
            logger.debug(f"Cache EXPIRE: {key} = {seconds}s")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache EXPIRE error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            await self._ensure_connected()
            
            result = await self._client.ttl(key)
            logger.debug(f"Cache TTL: {key} = {result}s")
            return result
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern.
        
        Args:
            pattern: Key pattern (default: all keys)
            
        Returns:
            List of matching keys
        """
        try:
            await self._ensure_connected()
            
            keys = await self._client.keys(pattern)
            logger.debug(f"Cache KEYS: {pattern} = {len(keys)} keys")
            return keys
            
        except Exception as e:
            logger.error(f"Cache KEYS error for pattern {pattern}: {e}")
            return []
    
    async def clear(self, pattern: str = "*") -> int:
        """Clear keys matching pattern.
        
        Args:
            pattern: Key pattern (default: all keys)
            
        Returns:
            Number of keys deleted
        """
        try:
            await self._ensure_connected()
            
            keys = await self.keys(pattern)
            if not keys:
                return 0
            
            result = await self._client.delete(*keys)
            logger.info(f"Cache CLEAR: {pattern} = {result} keys deleted")
            return result
            
        except Exception as e:
            logger.error(f"Cache CLEAR error for pattern {pattern}: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis.
        
        Returns:
            Health check results
        """
        try:
            await self._ensure_connected()
            
            # Test basic operations
            start_time = datetime.now()
            await self._client.ping()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = await self._client.info()
            
            return {
                "healthy": True,
                "status": "connected",
                "response_time_ms": round(response_time, 2),
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e),
                "connected": self._connected
            }


# Cache decorators for easy caching
def cache_result(cache_client: RedisCache, expire: int = 300):
    """Decorator to cache function results.
    
    Args:
        cache_client: Redis cache client
        expire: Cache expiration time in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"cache:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cached_result = await cache_client.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_client.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


# Global cache instance
_cache_client: Optional[RedisCache] = None


async def get_cache_client() -> RedisCache:
    """Get global cache client instance.
    
    Returns:
        Redis cache client
    """
    global _cache_client
    if _cache_client is None:
        import os
        _cache_client = RedisCache(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD"),
            db=int(os.environ.get("REDIS_DB", "0"))
        )
        await _cache_client.connect()
    
    return _cache_client


async def close_cache_client() -> None:
    """Close global cache client."""
    global _cache_client
    if _cache_client:
        await _cache_client.disconnect()
        _cache_client = None