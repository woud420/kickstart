"""PostgreSQL client helpers for {{ service_name }}."""

from collections.abc import Mapping

import asyncpg


async def create_pool(database_url: str) -> asyncpg.Pool:
    """Create an asyncpg connection pool."""
    return await asyncpg.create_pool(database_url)


async def close_pool(pool: asyncpg.Pool) -> None:
    """Close a database pool."""
    await pool.close()


async def health_check(pool: asyncpg.Pool) -> Mapping[str, str]:
    """Return a small database health payload."""
    async with pool.acquire() as connection:
        version = await connection.fetchval("select version()")
    return {
        "status": "ok",
        "database": "postgres",
        "version": str(version),
    }
