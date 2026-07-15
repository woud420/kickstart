"""CLI bodies of the read-only inspection verbs: plan, adopt tiers, export.

The integration suite runs these through the installed binary (a separate
process coverage cannot see); these tests drive the same command functions
in-process so the human/json output branches and exit codes stay covered.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.main import app
from src.generator.markers import fence
from src.generator.projections import scaffold_docs_projections
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldArtifacts, ScaffoldContract


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _service_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        artifacts=ScaffoldArtifacts(image="dockerfile"),
    )


def _managed_repo(root: Path) -> None:
    """A repo whose managed docs match the current standard byte-for-byte."""
    contract = _service_contract()
    (root / ".kickstart").mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_PATH).write_text(contract.manifest_json("planned"), encoding="utf-8")
    for projection in scaffold_docs_projections(contract):
        target = root / projection.target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(projection.content, encoding="utf-8")
    architecture = root / "docs" / "architecture" / "README.md"
    architecture.parent.mkdir(parents=True, exist_ok=True)
    architecture.write_text(fence("architecture-readme", "# planned Architecture\n"), encoding="utf-8")


def _conformant_repo(root: Path) -> None:
    """A Level 1 repo: the vendor-neutral artifact set, no manifest."""
    for directory in (
        ".agents/skills",
        "docs/architecture",
        "docs/contracts",
        "docs/operations",
        "docs/decisions",
        ".github/workflows",
    ):
        (root / directory).mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agent Map\n", encoding="utf-8")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    (root / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
    (root / ".github/workflows/ci.yml").write_text("name: ci\n", encoding="utf-8")


def test_version_flag_prints_and_exits(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "kickstart v" in result.stdout


def test_plan_reports_in_sync_repo(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)

    result = runner.invoke(app, ["plan", str(tmp_path)])

    assert result.exit_code == 0
    assert "Docs plan for" in result.stdout
    assert "in-sync" in result.stdout
    assert "presence-only" in result.stdout


def test_plan_json_is_machine_readable(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)

    result = runner.invoke(app, ["plan", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["in_sync"] is True
    assert {entry["artifact"] for entry in payload["entries"]} >= {"agent-map", "architecture-readme"}


def test_plan_prints_diff_for_fence_edits(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace("orientation surface", "renamed surface"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["plan", str(tmp_path)])

    assert result.exit_code == 1
    assert "content-drift" in result.stdout
    assert "renamed surface" in result.stdout


def test_plan_usage_error_without_manifest(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["plan", str(tmp_path)])

    assert result.exit_code == 2
    assert "cannot plan against" in result.stdout


def test_adopt_check_reports_levels_for_conformant_repo(runner: CliRunner, tmp_path: Path) -> None:
    _conformant_repo(tmp_path)

    result = runner.invoke(app, ["adopt", str(tmp_path), "--check"])

    assert result.exit_code == 0
    assert "achieved: conformant / claimed: conformant" in result.stdout
    assert "ok" in result.stdout


def test_adopt_check_names_gaps(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["adopt", str(tmp_path), "--check"])

    assert result.exit_code == 1
    assert "needed" in result.stdout
    assert "missing" in result.stdout


def test_adopt_without_check_is_a_usage_error(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["adopt", str(tmp_path)])

    assert result.exit_code == 2


def test_export_backstage_creates_then_reports_unchanged(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)

    created = runner.invoke(app, ["export", "backstage", str(tmp_path)])
    unchanged = runner.invoke(app, ["export", "backstage", str(tmp_path)])

    assert created.exit_code == 0
    assert "created" in created.stdout
    assert unchanged.exit_code == 0
    assert "unchanged" in unchanged.stdout
    assert (tmp_path / "catalog-info.yaml").is_file()


def test_export_backstage_refuses_unfenced_catalog(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)
    (tmp_path / "catalog-info.yaml").write_text("apiVersion: backstage.io/v1alpha1\n", encoding="utf-8")

    result = runner.invoke(app, ["export", "backstage", str(tmp_path)])

    assert result.exit_code == 1
    assert "refusing" in result.stdout


def test_export_backstage_usage_error_without_manifest(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(app, ["export", "backstage", str(tmp_path)])

    assert result.exit_code == 2
    assert "cannot export" in result.stdout


def test_export_backstage_warns_on_missing_required_lines(runner: CliRunner, tmp_path: Path) -> None:
    _managed_repo(tmp_path)
    # A fenced catalog whose user-owned area lacks the required spec lines:
    # the refresh rewrites only the derived fence, so the validation warning
    # path (exit 1 with warnings) is exercised.
    (tmp_path / "catalog-info.yaml").write_text(
        fence("catalog-derived", "apiVersion: backstage.io/v1alpha1\n", style="yaml"),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["export", "backstage", str(tmp_path)])

    assert result.exit_code == 1
    assert "warning" in result.stdout
