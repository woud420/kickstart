import json
from pathlib import Path

import pytest

from src.generator.adoption import (
    MANIFEST_PATH,
    STANDARD_ARTIFACTS,
    AdoptionTargetError,
    inspect_repo,
)


def scaffold_standard_repo(root: Path) -> None:
    manifest = {
        "schema_version": "3.0",
        "project": {"name": "demo", "kind": "cli", "repo_layout": "single-project"},
        "lifecycle": {"check": "make check"},
    }
    (root / ".kickstart").mkdir(parents=True)
    (root / MANIFEST_PATH).write_text(json.dumps(manifest), encoding="utf-8")
    for name in ("AGENTS.md", "README.md"):
        (root / name).write_text("content\n", encoding="utf-8")
    (root / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
    for directory in ("docs/architecture", "docs/contracts", "docs/operations", "docs/decisions", ".github/workflows"):
        (root / directory).mkdir(parents=True)


def test_inspect_repo_reports_complete_standard_repo(tmp_path: Path) -> None:
    scaffold_standard_repo(tmp_path)

    report = inspect_repo(tmp_path)

    assert report.complete
    assert report.missing == ()
    assert len(report.artifacts) == len(STANDARD_ARTIFACTS)


def test_inspect_repo_reports_missing_artifacts(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("only a readme\n", encoding="utf-8")

    report = inspect_repo(tmp_path)

    assert not report.complete
    missing_paths = {status.path for status in report.missing}
    assert MANIFEST_PATH in missing_paths
    assert "docs/decisions/" in missing_paths
    assert "README.md" not in missing_paths


def test_inspect_repo_flags_malformed_manifest(tmp_path: Path) -> None:
    scaffold_standard_repo(tmp_path)
    (tmp_path / MANIFEST_PATH).write_text("{not json", encoding="utf-8")

    report = inspect_repo(tmp_path)

    manifest_status = next(status for status in report.artifacts if status.path == MANIFEST_PATH)
    assert manifest_status.present
    assert "not valid JSON" in manifest_status.issue
    assert not report.complete


def test_inspect_repo_flags_manifest_missing_keys(tmp_path: Path) -> None:
    scaffold_standard_repo(tmp_path)
    (tmp_path / MANIFEST_PATH).write_text('{"schema_version": "3.0"}', encoding="utf-8")

    report = inspect_repo(tmp_path)

    manifest_status = next(status for status in report.artifacts if status.path == MANIFEST_PATH)
    assert "manifest missing keys: project, lifecycle" in manifest_status.issue


def test_inspect_repo_rejects_missing_target(tmp_path: Path) -> None:
    with pytest.raises(AdoptionTargetError, match="not an existing directory"):
        inspect_repo(tmp_path / "nope")


def test_makefile_without_check_target_is_flagged(tmp_path: Path) -> None:
    scaffold_standard_repo(tmp_path)
    (tmp_path / "Makefile").write_text("build:\n\ttrue\n", encoding="utf-8")

    report = inspect_repo(tmp_path)

    makefile_status = next(status for status in report.artifacts if status.path == "Makefile")
    assert makefile_status.present
    assert "no 'check' target" in makefile_status.issue
    assert not report.complete


def test_report_json_is_machine_readable(tmp_path: Path) -> None:
    scaffold_standard_repo(tmp_path)

    payload = json.loads(inspect_repo(tmp_path).to_json())

    assert payload["complete"] is True
    assert {entry["path"] for entry in payload["artifacts"]} == set(STANDARD_ARTIFACTS)
