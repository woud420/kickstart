"""Redis client helpers for {{ service_name }}."""

from collections.abc import Awaitable, Mapping

import redis.asyncio as redis


def create_client(redis_url: str) -> redis.Redis:
    """Create a Redis client from a URL."""
    return redis.from_url(redis_url, decode_responses=True)


async def close_client(client: redis.Redis) -> None:
    """Close a Redis client."""
    await client.aclose()


async def health_check(client: redis.Redis) -> Mapping[str, str]:
    """Return a small Redis health payload."""
    pong = await _resolve_bool(client.ping())
    return {
        "status": "ok" if pong else "unhealthy",
        "cache": "redis",
    }


async def _resolve_bool(value: bool | Awaitable[bool]) -> bool:
    """Resolve Redis methods that may be typed as sync or async."""
    if isinstance(value, bool):
        return value
    return await value
