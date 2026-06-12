"""Unit tests for the generated PostgreSQL helpers (no infrastructure required)."""

from types import TracebackType
from typing import cast

import asyncpg

from src.clients import database


class FakeConnection:
    """Stand-in for the single query the health check issues."""

    async def fetchval(self, query: str) -> str:
        assert query == "select version()"
        return "PostgreSQL 17.0 (fake)"


class FakeAcquire:
    async def __aenter__(self) -> FakeConnection:
        return FakeConnection()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class FakePool:
    """Stand-in for the asyncpg pool surface the helpers use."""

    def acquire(self) -> FakeAcquire:
        return FakeAcquire()


async def test_health_check_reports_server_version() -> None:
    payload = await database.health_check(cast(asyncpg.Pool, FakePool()))

    assert payload["status"] == "ok"
    assert payload["database"] == "postgres"
    assert "PostgreSQL" in payload["version"]
