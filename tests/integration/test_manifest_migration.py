"""Legacy migration through the user-facing CLI across supported project variants."""

from dataclasses import replace
import json
from pathlib import Path
import pytest

from src.generator.adoption import inspect_repo
from src.generator.scaffold_contract import ScaffoldContract
from tests.integration.conftest import KickstartRunner
from tests.integration.test_manifest_identity import CASES


@pytest.mark.parametrize("version", ["3.0", "3.1", "3.2"])
@pytest.mark.parametrize(("options", "language", "framework"), CASES)
def test_migrate_supported_legacy_variants_without_touching_other_files(
    version: str,
    options: tuple[str, ...],
    language: str | None,
    framework: str | None,
    kickstart_run: KickstartRunner,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    generated = kickstart_run(
        "create",
        options[0],
        "migrated",
        *options[1:],
        "--root",
        str(tmp_path),
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert generated.returncode == 0, generated.stderr
    root = tmp_path / "migrated"
    path = root / ".kickstart/scaffold.json"
    current = ScaffoldContract.from_manifest(json.loads(path.read_text()))
    old = replace(current, schema_version=version, project_kind="worker" if current.is_worker else current.project_kind)
    legacy = json.loads(old.manifest_json("migrated"))
    if version != "3.2":
        legacy["project"].pop("language", None)
        legacy["project"].pop("framework", None)
    path.write_text(json.dumps(legacy, indent=2) + "\n")
    if current.is_worker and current.language == "typescript":
        readme = root / "docs/contracts/README.md"
        readme.write_text(readme.read_text().replace("Kind: `service`", "Kind: `worker`"))
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    flags = [str(root), "--json"]
    if language:
        flags += ["--language", language]
    if framework:
        flags += ["--framework", framework]
    planned = kickstart_run("migrate", *flags, cwd=repo_root, capture_output=True, text=True)
    assert planned.returncode == 0, planned.stdout + planned.stderr
    plan = json.loads(planned.stdout)
    assert plan["ready"]
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    applied = kickstart_run(
        "migrate",
        *flags,
        "--apply",
        "--expected-sha256",
        plan["source_sha256"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["action"] == "applied"
    after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert {p for p in before if before[p] != after[p]} == {Path(".kickstart/scaffold.json")}
    assert after.keys() == before.keys()
    assert inspect_repo(root).complete
    final = json.loads(path.read_text())
    assert final["schema_version"] == "4.0" and final["project"].get("language") == language
    again = kickstart_run("migrate", str(root), "--apply", "--json", cwd=repo_root, capture_output=True, text=True)
    assert again.returncode == 0, again.stdout + again.stderr
    assert json.loads(again.stdout)["action"] == "unchanged"
    assert path.read_bytes() == after[Path(".kickstart/scaffold.json")]
