"""SQLite services keep their own seeds and declare only working support."""

import ast
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import pytest

from src.generator.scaffold_contract import ScaffoldContract
from src.generator.service import ServiceGenerator
from src.utils.errors import ExtensionError


@pytest.mark.parametrize("cache,auth", [(None, None), ("redis", "jwt")])
def test_python_sqlite_generation_has_working_metadata_and_seeds(
    tmp_path: Path, cache: str | None, auth: str | None
) -> None:
    ServiceGenerator(
        "local-api", "python", False, {}, root=str(tmp_path), database="sqlite", cache=cache, auth=auth
    ).create()
    project = tmp_path / "local-api"
    manifest = json.loads((project / ".kickstart/scaffold.json").read_text())
    contract = ScaffoldContract.from_manifest(manifest)

    assert manifest["schema_version"] == "4.0"
    assert contract.service_extensions.database == "sqlite"
    assert contract.service_extensions.cache == cache
    assert contract.service_extensions.auth == auth
    assert "aiosqlite>=0.22.1,<1" in (project / "requirements.txt").read_text()
    assert "asyncpg" not in (project / "requirements.txt").read_text()
    assert "sqlite_path: Path" in (project / "src/config/settings.py").read_text()
    environment = (project / ".env.example").read_text()
    assert "SQLITE_PATH=data/app.sqlite3" in environment
    assert "DB_HOST" not in environment and "{{" not in environment
    assert (project / "tests/unit/clients/__init__.py").is_file()
    assert "connect_database" in (project / "src/clients/database.py").read_text()
    assert "sqlite" in (project / "tests/unit/clients/test_database.py").read_text()
    assert (project / "docs/operations/sqlite.md").is_file()
    for name in [".gitignore", ".dockerignore"]:
        content = (project / name).read_text()
        assert "data/" in content and ".env" in content and "*.sqlite3" in content

    script = (project / "migrations/001_initial.sql").read_text()
    assert "gen_random_uuid" not in script and "JSONB" not in script
    with closing(sqlite3.connect(tmp_path / "migration-probe.sqlite3")) as connection:
        connection.executescript(script)
        connection.execute("INSERT INTO example_items (name) VALUES (?)", ("probe",))
        assert connection.execute("SELECT name FROM example_items").fetchone() == ("probe",)
    for path in project.rglob("*.py"):
        ast.parse(path.read_text())


@pytest.mark.parametrize(
    "language,runtime,framework",
    [
        ("typescript", "container", None),
        ("rust", "container", None),
        ("go", "container", None),
        ("cpp", "container", None),
        ("python", "container", "minimal"),
        ("typescript", "cloudflare-workers", None),
    ],
)
def test_sqlite_unsupported_profiles_fail_without_project_output(
    tmp_path: Path, language: str, runtime: str, framework: str | None
) -> None:
    generator = ServiceGenerator(
        "unsupported", language, False, {}, root=str(tmp_path), runtime=runtime, framework=framework, database="sqlite"
    )

    with pytest.raises(ExtensionError, match="database extension 'sqlite' is not supported"):
        generator.create()

    assert not (tmp_path / "unsupported").exists()
