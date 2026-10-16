"""Generated identity distinguishes scaffold choices without guessing legacy inputs."""

import json
from pathlib import Path

import pytest

from src.generator.adoption import inspect_repo
from src.generator.docs_plan import inspect_docs
from src.generator.scaffold_contract import ScaffoldContract
from tests.integration.conftest import KickstartRunner


CASES = (
    (("service", "--lang", "python"), "python", "fastapi"),
    (("service", "--lang", "python", "--framework", "minimal"), "python", "minimal"),
    (("service", "--lang", "go"), "go", None),
    (("service", "--lang", "rust"), "rust", None),
    (("service", "--lang", "ts"), "typescript", None),
    (("service", "--lang", "cpp"), "cpp", None),
    (("service", "--lang", "ts", "--runtime", "cloudflare-workers"), "typescript", None),
    (("service", "--lang", "rust", "--runtime", "cloudflare-workers"), "rust", None),
    (("lib", "--lang", "python"), "python", None),
    (("lib", "--lang", "rust"), "rust", None),
    (("cli", "--lang", "python"), "python", "typer"),
    (("cli", "--lang", "rust"), "rust", "clap"),
    (("cli", "--lang", "ts"), "typescript", "oclif"),
    (("frontend",), "typescript", "react"),
    (("system", "--knowledge", "none"), None, None),
    (("system", "--knowledge", "none", "--workspace-tooling", "bun-turbo"), None, None),
)


@pytest.mark.parametrize(("options", "language", "framework"), CASES)
def test_generated_manifest_records_identity(
    options: tuple[str, ...],
    language: str | None,
    framework: str | None,
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    completed = kickstart_run(
        "create",
        options[0],
        "identified",
        *options[1:],
        "--root",
        str(tmp_path),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, f"{completed.stdout}{completed.stderr}"
    root = tmp_path / "identified"
    manifest = json.loads((root / ".kickstart/scaffold.json").read_text())
    assert manifest["schema_version"] == "3.2"
    project = manifest["project"]

    assert project.get("language") == language
    assert project.get("framework") == framework
    if language is None:
        assert "language" not in project and "framework" not in project
    if options[0] == "cli":
        assert project["framework"] == project["cli_framework"]
    rebuilt = ScaffoldContract.from_manifest(manifest).manifest("identified")
    assert rebuilt["project"] == project
    assert inspect_repo(root).complete
    assert inspect_docs(root).in_sync
