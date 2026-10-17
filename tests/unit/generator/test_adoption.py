"""Tiered adoption check: Level 1 conformant, Level 2 managed."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

import src.generator.adoption as adoption

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
        language="python",
        framework="typer",
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


@pytest.mark.parametrize("ownership", [{}, {"AGENTS.md": "seed"}])
def test_recorded_seed_and_unlisted_docs_do_not_claim_fences(tmp_path: Path, ownership: dict[str, str]) -> None:
    scaffold_managed_repo(tmp_path)
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["ownership"] = ownership
    manifest_path.write_text(json.dumps(manifest))
    (tmp_path / "AGENTS.md").write_text("Human-authored instructions stay here.\n")
    (tmp_path / "CLAUDE.md").write_text("<!-- kickstart:begin claude-pointer -->\nunlisted and malformed\n")

    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = inspect_repo(tmp_path)

    assert report.complete
    assert report.claimed_level == report.achieved_level == "managed"
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("owned_body", ["human prose without a fence\n", "<!-- kickstart:begin contracts-readme -->\n"])
def test_recorded_managed_doc_still_requires_healthy_fences(tmp_path: Path, owned_body: str) -> None:
    scaffold_managed_repo(tmp_path)
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["ownership"] = {"AGENTS.md": "seed", "docs/contracts/README.md": "contracts-readme"}
    manifest_path.write_text(json.dumps(manifest))
    (tmp_path / "AGENTS.md").write_text("Human-authored instructions stay here.\n")
    (tmp_path / "docs/contracts/README.md").write_text(owned_body)

    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.achieved_level == "conformant"
    assert "docs/contracts/README.md" in next(s.issue for s in report.missing if s.path == "managed docs fences")


def test_recorded_owned_fence_and_seed_docs_can_coexist(tmp_path: Path) -> None:
    scaffold_managed_repo(tmp_path)
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["ownership"] = {"AGENTS.md": "seed", "docs/contracts/README.md": "contracts-readme"}
    manifest_path.write_text(json.dumps(manifest))
    (tmp_path / "AGENTS.md").write_text("Human-authored instructions stay here.\n")

    assert inspect_repo(tmp_path).complete


@pytest.mark.parametrize("schema", ["3.0", "3.1", "3.2"])
def test_legacy_manifest_does_not_use_new_ownership_to_skip_fences(tmp_path: Path, schema: str) -> None:
    scaffold_managed_repo(tmp_path)
    manifest = replace(_cli_contract(), schema_version=schema).manifest("demo")
    manifest["ownership"] = {"AGENTS.md": "seed"}
    (tmp_path / MANIFEST_PATH).write_text(json.dumps(manifest))
    (tmp_path / "AGENTS.md").write_text("Legacy unfenced instructions\n")

    assert not inspect_repo(tmp_path).complete


def test_recorded_seed_does_not_skip_level_one_presence(tmp_path: Path) -> None:
    scaffold_managed_repo(tmp_path)
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["ownership"] = {"AGENTS.md": "seed"}
    manifest_path.write_text(json.dumps(manifest))
    (tmp_path / "AGENTS.md").unlink()

    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.achieved_level == "below-standard"


@pytest.mark.parametrize("replacement", [None, "invalid json"])
def test_manifest_changed_before_fence_check_fails_closed(tmp_path: Path, monkeypatch, replacement: str | None) -> None:
    scaffold_managed_repo(tmp_path)
    original = adoption._fence_readiness_status

    def changed_manifest(root: Path):
        path = root / MANIFEST_PATH
        if replacement is None:
            path.unlink()
        else:
            path.write_text(replacement)
        return original(root)

    monkeypatch.setattr(adoption, "_fence_readiness_status", changed_manifest)
    report = inspect_repo(tmp_path)

    assert not report.complete
    assert report.achieved_level == "conformant"
    assert any(s.path == "managed docs fences" and "manifest cannot drive" in s.issue for s in report.missing)
