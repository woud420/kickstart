"""SQLite capability tests use real files without external infrastructure."""

from pathlib import Path

import aiosqlite
import pytest

from src.clients.database import connect_database, health_check
from src.config.settings import Settings

MIGRATION = Path(__file__).resolve().parents[3] / "migrations/001_initial.sql"


async def initialize(connection: aiosqlite.Connection) -> None:
    cursor = await connection.executescript(MIGRATION.read_text())
    await cursor.close()


async def test_sqlite_committed_data_survives_reopening(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "app.sqlite3"
    assert not path.exists()
    async with connect_database(path) as connection:
        await initialize(connection)
        await connection.execute_insert("INSERT INTO example_items (name) VALUES (?)", ("saved",))
        await connection.commit()
        assert await health_check(connection) == {"status": "ok", "database": "sqlite"}
    async with connect_database(path) as reopened:
        assert await reopened.execute_fetchall("SELECT name FROM example_items") == [("saved",)]
    with pytest.raises(ValueError, match="no active connection"):
        await connection.execute("SELECT 1")


async def test_sqlite_uncommitted_data_is_not_saved_on_close(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    async with connect_database(path) as connection:
        await initialize(connection)
        await connection.execute_insert(
            "INSERT INTO example_items (name) VALUES (?)", ("unfinished",)
        )
    async with connect_database(path) as reopened:
        assert await reopened.execute_fetchall("SELECT name FROM example_items") == []


async def test_sqlite_foreign_keys_are_enabled_for_each_connection(tmp_path: Path) -> None:
    path = tmp_path / "app.sqlite3"
    for _ in range(2):
        async with connect_database(path) as connection:
            await initialize(connection)
            cursor = await connection.execute(
                "CREATE TABLE IF NOT EXISTS child (item_id INTEGER REFERENCES example_items(id))"
            )
            await cursor.close()
            with pytest.raises(aiosqlite.IntegrityError):
                await connection.execute_insert("INSERT INTO child VALUES (?)", (999,))


async def test_sqlite_context_closes_after_query_failure(tmp_path: Path) -> None:
    with pytest.raises(aiosqlite.IntegrityError):
        async with connect_database(tmp_path / "app.sqlite3") as connection:
            await initialize(connection)
            await connection.execute_insert("INSERT INTO example_items (name) VALUES (?)", (None,))
    with pytest.raises(ValueError, match="no active connection"):
        await connection.execute("SELECT 1")


async def test_sqlite_invalid_file_target_fails(tmp_path: Path) -> None:
    with pytest.raises(aiosqlite.OperationalError):
        async with connect_database(tmp_path):
            pytest.fail("a directory cannot be opened as a database")


def test_sqlite_path_can_be_configured_without_opening_a_database(
    tmp_path: Path, monkeypatch
) -> None:
    path = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("SQLITE_PATH", str(path))
    assert Settings().sqlite_path == path
    assert not path.exists()
