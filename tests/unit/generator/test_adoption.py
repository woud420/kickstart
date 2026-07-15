"""Tiered adoption check: Level 1 conformant, Level 2 managed."""

import json
from pathlib import Path

import pytest

from src.generator.adoption import (
    LEVEL1_ARTIFACTS,
    MANIFEST_PATH,
    STANDARD_ARTIFACTS,
    AdoptionTargetError,
    inspect_repo,
)
from src.generator.markers import fence
from src.generator.projections import scaffold_docs_projections
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract


def _cli_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="cli",
        execution_models=("cli",),
        runtime_platforms=("local",),
        artifacts=ScaffoldArtifacts(package="pyproject"),
        cli_framework="typer",
    )


def scaffold_conformant_repo(root: Path) -> None:
    """Write the vendor-neutral Level 1 artifact set, no manifest."""
    for name in ("AGENTS.md", "README.md"):
        (root / name).write_text("content\n", encoding="utf-8")
    (root / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
    for directory in (
        ".agents/skills",
        "docs/architecture",
        "docs/contracts",
        "docs/operations",
        "docs/decisions",
        ".github/workflows",
    ):
        (root / directory).mkdir(parents=True)
    (root / ".github/workflows/ci.yml").write_text("name: ci\n", encoding="utf-8")


def scaffold_managed_repo(root: Path) -> None:
    """Write a Level 2 repo: conformant plus a manifest that drives fenced docs."""
    scaffold_conformant_repo(root)
    contract = _cli_contract()
    (root / ".kickstart").mkdir(parents=True)
    (root / MANIFEST_PATH).write_text(contract.manifest_json("demo"), encoding="utf-8")
    for projection in scaffold_docs_projections(contract):
        path = root / projection.target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(projection.content, encoding="utf-8")
    (root / "docs/architecture/README.md").write_text(
        fence("architecture-readme", "# demo Architecture\n"), encoding="utf-8"
    )


def test_conformant_repo_without_manifest_is_complete(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)

    report = inspect_repo(tmp_path)

    assert report.complete
    assert report.achieved_level == "conformant"
    assert report.claimed_level == "conformant"
    assert report.missing == ()
    assert len(report.artifacts) == len(LEVEL1_ARTIFACTS)


def test_managed_repo_is_complete_at_level_two(tmp_path: Path) -> None:
    scaffold_managed_repo(tmp_path)

    report = inspect_repo(tmp_path)

    assert report.complete
    assert report.achieved_level == "managed"
    assert report.claimed_level == "managed"
    assert report.missing == ()


def test_manifest_with_unfenced_docs_fails_its_managed_claim(tmp_path: Path) -> None:
    scaffold_managed_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("hand-written, no fences\n", encoding="utf-8")

    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.achieved_level == "conformant"
    assert report.claimed_level == "managed"
    fence_status = next(status for status in report.missing if status.path == "managed docs fences")
    assert "AGENTS.md (unfenced)" in fence_status.issue


def test_missing_manifest_is_not_a_gap(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("only a readme\n", encoding="utf-8")

    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.achieved_level == "below-standard"
    missing_paths = {status.path for status in report.missing}
    assert MANIFEST_PATH not in missing_paths
    assert "docs/decisions/" in missing_paths
    assert ".agents/skills/" in missing_paths
    assert "README.md" not in missing_paths


def test_inspect_repo_flags_malformed_manifest(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)
    (tmp_path / ".kickstart").mkdir(parents=True)
    (tmp_path / MANIFEST_PATH).write_text("{not json", encoding="utf-8")

    report = inspect_repo(tmp_path)

    manifest_status = next(status for status in report.artifacts if status.path == MANIFEST_PATH)
    assert manifest_status.present
    assert "not valid JSON" in manifest_status.issue
    assert report.claimed_level == "managed"
    assert report.achieved_level == "conformant"
    assert not report.complete


def test_inspect_repo_flags_manifest_missing_keys(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)
    (tmp_path / ".kickstart").mkdir(parents=True)
    (tmp_path / MANIFEST_PATH).write_text(json.dumps({"schema_version": "3.0"}), encoding="utf-8")

    report = inspect_repo(tmp_path)

    manifest_status = next(status for status in report.artifacts if status.path == MANIFEST_PATH)
    assert "manifest missing keys" in manifest_status.issue
    assert not report.complete


def test_manifest_path_occupied_by_a_directory_fails_its_claim(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)
    (tmp_path / MANIFEST_PATH).mkdir(parents=True)

    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.claimed_level == "managed"
    manifest_status = next(status for status in report.artifacts if status.path == MANIFEST_PATH)
    assert not manifest_status.ok


def test_inspect_repo_rejects_missing_target(tmp_path: Path) -> None:
    with pytest.raises(AdoptionTargetError):
        inspect_repo(tmp_path / "does-not-exist")


def test_makefile_without_check_target_is_flagged(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)
    (tmp_path / "Makefile").write_text("build:\n\ttrue\n", encoding="utf-8")

    report = inspect_repo(tmp_path)

    makefile_status = next(status for status in report.artifacts if status.path == "Makefile")
    assert makefile_status.present
    assert "check" in makefile_status.issue
    assert not report.complete


def test_report_json_is_machine_readable(tmp_path: Path) -> None:
    scaffold_managed_repo(tmp_path)

    payload = json.loads(inspect_repo(tmp_path).to_json())

    assert payload["complete"] is True
    assert payload["achieved_level"] == "managed"
    assert payload["claimed_level"] == "managed"
    paths = {entry["path"] for entry in payload["artifacts"]}
    assert set(LEVEL1_ARTIFACTS) <= paths
    assert MANIFEST_PATH in paths
    assert "managed docs fences" in paths
    levels = {entry["path"]: entry["level"] for entry in payload["artifacts"]}
    assert levels["AGENTS.md"] == "conformant"
    assert levels[MANIFEST_PATH] == "managed"
    assert set(STANDARD_ARTIFACTS) == set(LEVEL1_ARTIFACTS) | {MANIFEST_PATH}


def test_empty_workflows_directory_is_not_conformant(tmp_path: Path) -> None:
    scaffold_conformant_repo(tmp_path)
    (tmp_path / ".github/workflows/ci.yml").unlink()

    report = inspect_repo(tmp_path)

    assert not report.complete
    status = next(artifact for artifact in report.artifacts if artifact.path == ".github/workflows/")
    assert not status.ok
    assert "no workflow file" in status.issue
