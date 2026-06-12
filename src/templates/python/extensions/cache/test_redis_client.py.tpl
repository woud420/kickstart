"""Unit tests for the generated Redis cache helpers (no infrastructure required)."""

from typing import cast

import redis.asyncio as redis

from src.clients import cache


class FakeRedis:
    """In-memory stand-in for the Redis surface the helpers use."""

    def __init__(self, *, alive: bool) -> None:
        self._alive = alive

    def ping(self) -> bool:
        return self._alive


def test_create_client_parses_url_without_connecting() -> None:
    client = cache.create_client("redis://cache-host:6380/2")
    kwargs = client.connection_pool.connection_kwargs

    assert kwargs["host"] == "cache-host"
    assert kwargs["port"] == 6380
    assert kwargs["db"] == 2


async def test_health_check_reports_ok_when_redis_answers() -> None:
    payload = await cache.health_check(cast(redis.Redis, FakeRedis(alive=True)))

    assert payload == {"status": "ok", "cache": "redis"}


async def test_health_check_reports_unhealthy_when_ping_fails() -> None:
    payload = await cache.health_check(cast(redis.Redis, FakeRedis(alive=False)))

    assert payload["status"] == "unhealthy"
