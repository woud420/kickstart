"""Executed inside a generated project by test_python_postgres.py."""

import asyncio
import json
import os
from pathlib import Path
import secrets
import sys
from uuid import UUID, uuid4

import asyncpg
from fastapi.testclient import TestClient
import pytest

from src.clients.database import close_pool, create_pool, health_check
from src.main import create_app


def check_http_and_jwt() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/users", json={"email": "http@example.com"})
        assert response.status_code == 201
        user = response.json()
        assert client.get(f"/users/{user['id']}").json() == user
        assert client.get(f"/users/{uuid4()}").status_code == 404
        paths = client.get("/openapi.json").json()["paths"]
        assert not any("login" in path or "signup" in path for path in paths)
    if sys.argv[1] == "jwt":
        from src.handler.auth import JWTAuth

        auth = JWTAuth(secrets.token_urlsafe(32))
        hashed = auth.hash_password("Example-password-123")
        assert hashed != "Example-password-123"
        assert auth.verify_password("Example-password-123", hashed)
        assert not auth.verify_password("incorrect", hashed)
        token = auth.create_access_token(user["id"])
        assert auth.verify_access_token(token) == {"subject": user["id"], "token_type": "access"}
        assert auth.verify_access_token("invalid.token") is None


async def check_database() -> None:
    pool = await create_pool(os.environ["KICKSTART_TEST_POSTGRES_DSN"])
    try:
        health = await health_check(pool)
        assert health["status"] == "ok" and health["database"] == "postgres"
        assert "PostgreSQL" in health["version"]
        async with pool.acquire() as connection:
            transaction = connection.transaction()
            await transaction.start()
            try:
                schema = "probe_" + uuid4().hex
                await connection.execute(f'CREATE SCHEMA "{schema}"')
                await connection.execute(f'SET LOCAL search_path TO "{schema}", public')
                await connection.execute(Path("migrations/001_initial.sql").read_text())
                check_http_and_jwt()
                assert await connection.fetchval("SELECT count(*) FROM users") == 0

                user = await connection.fetchrow(
                    "INSERT INTO users (username, email, profile_data, updated_at) "
                    "VALUES ('probe', 'probe@example.com', $1, '2000-01-01') RETURNING *",
                    json.dumps({"theme": "dark"}),
                )
                assert isinstance(user["id"], UUID)
                assert user["is_active"] and user["created_at"] is not None
                assert json.loads(user["profile_data"]) == {"theme": "dark"}
                user_id = user["id"]
                assert await connection.fetchval("SELECT id FROM active_users") == user_id
                await connection.execute(
                    "INSERT INTO user_profiles (user_id, bio, updated_at) VALUES ($1, 'Before', '2000-01-01')",
                    user_id,
                )
                await connection.execute("UPDATE user_profiles SET bio = 'After' WHERE user_id = $1", user_id)
                assert await connection.fetchval("SELECT updated_at > '2000-01-01' FROM user_profiles")

                # Savepoints keep rejected writes from aborting the outer test transaction.
                rejected = [
                    (
                        "INSERT INTO users (username, email) VALUES ('ab', 'valid@example.com')",
                        asyncpg.CheckViolationError,
                    ),
                    ("INSERT INTO users (username, email) VALUES ('valid', 'invalid')", asyncpg.CheckViolationError),
                    (
                        "INSERT INTO users (username, email) VALUES ('probe', 'other@example.com')",
                        asyncpg.UniqueViolationError,
                    ),
                    (
                        "INSERT INTO users (username, email) VALUES ('other', 'probe@example.com')",
                        asyncpg.UniqueViolationError,
                    ),
                    ("INSERT INTO users (email) VALUES ('only-email@example.com')", asyncpg.NotNullViolationError),
                    (
                        "INSERT INTO user_profiles (user_id) VALUES (uuid_generate_v4())",
                        asyncpg.ForeignKeyViolationError,
                    ),
                ]
                for statement, error in rejected:
                    with pytest.raises(error):
                        async with connection.transaction():
                            await connection.execute(statement)

                await connection.execute(
                    "UPDATE users SET is_active = false, last_login_at = NOW() WHERE id = $1", user_id
                )
                assert await connection.fetchval("SELECT updated_at FROM users") > user["updated_at"]
                assert await connection.fetchval("SELECT count(*) FROM active_users") == 0
                stats = await connection.fetchrow("SELECT * FROM user_stats")
                assert dict(stats) == {
                    "total_users": 1,
                    "active_users": 0,
                    "inactive_users": 1,
                    "users_with_login": 1,
                    "new_users_30d": 1,
                    "active_users_30d": 1,
                }
                await connection.execute("DELETE FROM users WHERE id = $1", user_id)
                assert await connection.fetchval("SELECT count(*) FROM user_profiles") == 0
            finally:
                await transaction.rollback()
    finally:
        await close_pool(pool)
    assert pool.is_closing()


if __name__ == "__main__":
    asyncio.run(check_database())
