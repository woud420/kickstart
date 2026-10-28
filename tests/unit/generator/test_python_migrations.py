"""Python services ship the migration of the database they were generated for."""

from pathlib import Path

from src.generator.service import ServiceGenerator


def _migration(tmp_path: Path, database: str | None) -> str:
    ServiceGenerator("svc", "python", False, {}, root=str(tmp_path), database=database).create()
    return (tmp_path / "svc" / "migrations" / "001_initial.sql").read_text()


def test_postgres_service_ships_the_extension_migration(tmp_path: Path) -> None:
    migration = _migration(tmp_path, "postgres")

    assert migration.startswith("-- Database migrations for svc\n")
    assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' in migration
    assert "CREATE TABLE IF NOT EXISTS user_profiles" in migration


def test_service_without_a_database_extension_ships_the_core_migration(tmp_path: Path) -> None:
    migration = _migration(tmp_path, None)

    assert migration.startswith("-- Initial database schema\n")
    assert "user_profiles" not in migration
