"""Manifest migration is an explicit CLI operation (ENG-629)."""

import json
from pathlib import Path
from typer.testing import CliRunner

from src.cli.main import app
from src.generator.scaffold_contract import ScaffoldContract

runner = CliRunner()


def legacy(root: Path) -> Path:
    path = root / ".kickstart/scaffold.json"
    path.parent.mkdir()
    contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        schema_version="3.0",
        generated_by="kickstart",
    )
    path.write_text(contract.manifest_json("legacy"))
    return path


def test_migrate_plans_by_default_and_requires_resolved_inputs(tmp_path: Path) -> None:
    path = legacy(tmp_path)
    original = path.read_bytes()
    result = runner.invoke(app, ["migrate", str(tmp_path), "--json"])
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert not payload["ready"]
    assert any(item["path"] == "project.language" for item in payload["diagnostics"])
    assert path.read_bytes() == original


def test_cli_explicit_resolution_plan_then_apply_is_idempotent(tmp_path: Path) -> None:
    path = legacy(tmp_path)
    original = path.read_bytes()
    flags = [str(tmp_path), "--language", "python", "--framework", "minimal", "--json"]
    planned = runner.invoke(app, ["migrate", *flags])
    assert planned.exit_code == 0, planned.output
    assert json.loads(planned.output)["ready"]
    assert path.read_bytes() == original
    applied = runner.invoke(app, ["migrate", *flags, "--apply"])
    assert applied.exit_code == 0, applied.output
    assert json.loads(applied.output)["action"] == "applied"
    migrated = path.read_bytes()
    repeated = runner.invoke(app, ["migrate", str(tmp_path), "--apply", "--json"])
    assert repeated.exit_code == 0, repeated.output
    assert json.loads(repeated.output)["action"] == "unchanged"
    assert path.read_bytes() == migrated


def test_cli_bad_target_is_a_usage_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["migrate", str(tmp_path / "missing")])
    assert result.exit_code == 2
    assert "migration target" in result.output


def test_human_plan_and_apply_explain_the_action(tmp_path: Path) -> None:
    path = legacy(tmp_path)
    original = path.read_bytes()
    planned = runner.invoke(app, ["migrate", str(tmp_path), "--language", "go"])
    assert planned.exit_code == 0, planned.output
    assert "Ready; pass --apply" in planned.output and "+++" in planned.output
    assert path.read_bytes() == original
    applied = runner.invoke(app, ["migrate", str(tmp_path), "--language", "go", "--apply"])
    assert applied.exit_code == 0 and "applied" in applied.output


def test_cli_reviewed_hash_mismatch_preserves_source(tmp_path: Path) -> None:
    path = legacy(tmp_path)
    original = path.read_bytes()
    result = runner.invoke(
        app, ["migrate", str(tmp_path), "--language", "go", "--apply", "--expected-sha256", "0" * 64]
    )
    assert result.exit_code == 2 and "reviewed SHA-256" in result.output
    assert path.read_bytes() == original
