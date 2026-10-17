"""JWT selection is a real TypeScript container capability, with optional Postgres."""

import json
from pathlib import Path

import pytest

from jsonschema import validate

from scripts.bootstrap_eval import audit_capability_tests
from src.api import create_service
from tests.integration.conftest import KickstartRunner


@pytest.mark.parametrize("database", [None, "postgres"])
@pytest.mark.parametrize("entrypoint", ["api", "cli"])
def test_typescript_jwt_scaffold(
    database: str | None,
    entrypoint: str,
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    if entrypoint == "api":
        create_service("jwt-api", "ts", False, {}, root=str(tmp_path), database=database, auth="jwt")
    else:
        args = ["create", "service", "jwt-api", "--lang", "ts", "--auth", "jwt"]
        if database is not None:
            args.extend(["--database", database])
        completed = kickstart_run(*args, "--root", str(tmp_path), cwd=repo_root, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr

    project = tmp_path / "jwt-api"
    manifest = json.loads((project / ".kickstart/scaffold.json").read_text())
    schema = json.loads((repo_root / "docs/contracts/scaffold-4.0.schema.json").read_text())
    validate(manifest, schema)
    expected_extensions = {"auth": "jwt"}
    if database is not None:
        expected_extensions["database"] = database
    assert manifest["extensions"] == expected_extensions
    assert manifest["project"]["language"] == "typescript"
    assert manifest["execution"]["models"] == ["container"]
    package = json.loads((project / "package.json").read_text())
    assert "jose" in package["dependencies"]
    assert ("pg" in package["dependencies"]) == (database is not None)
    assert (project / "src/handler/auth.ts").is_file()
    assert (project / "tests/auth.test.ts").is_file()
    assert "JWT_SECRET=\n" in (project / ".env.example").read_text()
    assert "JWT_ALGORITHM=HS256" in (project / ".env.example").read_text()
    assert "JWT_ISSUER=jwt-api" in (project / ".env.example").read_text()
    assert ("DATABASE_URL=" in (project / ".env.example").read_text()) == (database is not None)
    assert "createJwtAuth" in (project / "README.md").read_text()
    assert audit_capability_tests(project) == ()


def test_typescript_without_auth_keeps_the_minimal_scaffold(
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    completed = kickstart_run(
        "create",
        "service",
        "plain-api",
        "--lang",
        "typescript",
        "--root",
        str(tmp_path),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    project = tmp_path / "plain-api"
    package = json.loads((project / "package.json").read_text())
    assert "jose" not in package["dependencies"]
    assert not (project / "src/handler/auth.ts").exists()
    assert not (project / "tests/auth.test.ts").exists()
    assert "JWT_" not in (project / ".env.example").read_text()
    assert "loadJwtConfig" not in (project / "src/config/env.ts").read_text()
