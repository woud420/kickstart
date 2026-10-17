"""Asynchronous SQLite connection helpers for {{ service_name }}."""

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite


@asynccontextmanager
async def connect_database(path: Path) -> AsyncIterator[aiosqlite.Connection]:
    """Open a file database; callers explicitly commit or roll back writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as connection:
        cursor = await connection.execute("PRAGMA foreign_keys = ON")
        await cursor.close()
        yield connection


async def health_check(connection: aiosqlite.Connection) -> Mapping[str, str]:
    """Verify the connection can execute a query without applying migrations."""
    async with connection.execute("SELECT 1") as cursor:
        await cursor.fetchone()
    return {"status": "ok", "database": "sqlite"}
