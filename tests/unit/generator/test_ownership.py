"""Persisted ownership bounds read-only planning (ENG-630)."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.cli.main import app
from src.generator.service import ServiceGenerator
from src.generator.ownership_check import inspect_ownership
from src.generator.docs_plan import inspect_docs
from src.generator.manifest_migration import plan_migration, apply_migration
from src.generator.scaffold_contract import ScaffoldContract
from src.utils.errors import OwnershipPlanTargetError
from dataclasses import replace


def generate(root: Path) -> Path:
    ServiceGenerator("owned", "python", False, {}, root=str(root)).create()
    return root / "owned"


def test_fresh_generation_records_owned_regions_structural_facts_and_seeds(tmp_path: Path) -> None:
    root = generate(tmp_path)
    manifest = json.loads((root / ".kickstart/scaffold.json").read_text())
    ownership = manifest["ownership"]
    assert ownership["AGENTS.md"] == "agent-map"
    assert ownership["docs/architecture/README.md"] == "architecture-readme"
    assert ownership["Makefile"] == "make-check"
    assert ownership["src/main.py"] == "seed"
    assert not any("hash" in tag for tag in ownership.values())


def test_existing_plan_command_exercises_recorded_ownership(tmp_path: Path) -> None:
    root = generate(tmp_path)
    result = CliRunner().invoke(app, ["plan", str(root), "--ownership", "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["recorded"] and report["in_sync"]
    assert report["seeds_excluded"] > 0


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def load(root: Path) -> tuple[Path, dict]:
    path = root / ".kickstart/scaffold.json"
    return path, json.loads(path.read_text())


def test_index_covers_late_setup_files_and_is_deterministic(tmp_path: Path) -> None:
    root = generate(tmp_path)
    _, manifest = load(root)
    expected = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() or p.is_symlink()}
    assert set(manifest["ownership"]) == expected
    assert "src/routes/__init__.py" in manifest["ownership"]
    parsed = ScaffoldContract.from_manifest(manifest)
    assert json.loads(parsed.manifest_json("owned")) == manifest


def test_seed_and_user_owned_edits_are_excluded_without_writes(tmp_path: Path, monkeypatch) -> None:
    root = generate(tmp_path)
    seed = root / "src/main.py"
    seed.write_text("user application code\n")
    agents = root / "AGENTS.md"
    agents.write_text(agents.read_text() + "\nHuman-owned note: keep it.\n")
    before = snapshot(root)
    read = Path.read_text

    def guarded(path, *args, **kwargs):
        if path == seed:
            raise AssertionError("seed content must not be read")
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    report = inspect_ownership(root)
    assert report.in_sync
    assert not any("Human-owned" in entry.diff for entry in report.entries)
    assert snapshot(root) == before


def test_owned_region_drift_is_reported_only_inside_the_fence(tmp_path: Path) -> None:
    root = generate(tmp_path)
    agents = root / "AGENTS.md"
    agents.write_text(
        agents.read_text().replace("orientation surface", "changed managed text") + "\nPrivate outside note\n"
    )
    before = snapshot(root)
    report = inspect_ownership(root)
    entry = next(e for e in report.entries if e.target == "AGENTS.md")
    assert not report.in_sync and entry.status == "content-drift"
    assert "changed managed text" in entry.diff and "Private outside" not in entry.diff
    assert snapshot(root) == before


def test_stored_seed_downgrade_controls_which_paths_are_read(tmp_path: Path, monkeypatch) -> None:
    root = generate(tmp_path)
    path, manifest = load(root)
    manifest["ownership"]["AGENTS.md"] = "seed"
    path.write_text(json.dumps(manifest))
    read = Path.read_text

    def guarded(target, *args, **kwargs):
        if target == root / "AGENTS.md":
            raise AssertionError("excluded path read")
        return read(target, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    report = inspect_ownership(root)
    assert report.in_sync and not any(e.target == "AGENTS.md" for e in report.entries)


def test_co_owned_customizations_are_structural_only(tmp_path: Path) -> None:
    root = generate(tmp_path)
    makefile = root / "Makefile"
    makefile.write_text(
        makefile.read_text().replace("check:", "check verify:") + "\nuser-task:\n\t@echo human custom command\n"
    )
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text("name: human customized workflow\n")
    report = inspect_ownership(root)
    assert report.in_sync
    for target in ("Makefile", ".github/workflows/ci.yml"):
        entry = next(e for e in report.entries if e.target == target)
        assert entry.status == "presence-only" and not entry.diff


@pytest.mark.parametrize("makefile", ["check := something\n", "check\n: other\n", "other:\n\tcheck: pretend\n"])
def test_make_structural_check_does_not_invent_a_target(makefile: str, tmp_path: Path) -> None:
    root = generate(tmp_path)
    (root / "Makefile").write_text(makefile)
    report = inspect_ownership(root)
    assert next(e for e in report.entries if e.target == "Makefile").status == "structural-gap"


@pytest.mark.parametrize("target", ["AGENTS.md", "Makefile", ".github/workflows/ci.yml"])
def test_missing_owned_artifact_is_reported(tmp_path: Path, target: str) -> None:
    root = generate(tmp_path)
    (root / target).unlink()
    report = inspect_ownership(root)
    assert not report.in_sync
    assert next(e for e in report.entries if e.target == target).status == "would-create"


@pytest.mark.parametrize(
    "bad_path",
    [
        "../outside",
        "/outside",
        "C:/outside",
        "src\\main.py",
        "src//main.py",
        "src/./main.py",
        "src/../main.py",
        "AGENTS.md\n",
    ],
)
def test_malformed_recorded_paths_are_refused_without_reading_them(tmp_path: Path, bad_path: str) -> None:
    root = generate(tmp_path)
    path, manifest = load(root)
    manifest["ownership"][bad_path] = "seed"
    path.write_text(json.dumps(manifest))
    before = path.read_bytes()
    with pytest.raises(OwnershipPlanTargetError):
        inspect_ownership(root)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "target,record",
    [
        ("src/main.py", "agent-map"),
        ("Makefile", "agent-map"),
        ("AGENTS.md", None),
        ("AGENTS.md", "contracts-readme"),
        ("AGENTS.md", "unknown"),
        ("docs/architecture/README.md", "agent-map"),
    ],
)
def test_unsupported_classifications_or_region_promotions_are_refused(
    tmp_path: Path, target: str, record: str | None
) -> None:
    root = generate(tmp_path)
    path, manifest = load(root)
    manifest["ownership"][target] = record
    path.write_text(json.dumps(manifest))
    with pytest.raises(OwnershipPlanTargetError):
        inspect_ownership(root)


def test_migration_does_not_invent_ownership_from_existing_files(tmp_path: Path) -> None:
    root = generate(tmp_path)
    path, manifest = load(root)
    old = replace(ScaffoldContract.from_manifest(manifest), schema_version="3.2")
    path.write_text(old.manifest_json("owned"))
    (root / "user-added.py").write_text("we own this\n")
    plan = plan_migration(root)
    assert plan.ready
    assert "ownership" not in json.loads(plan.target_json)
    apply_migration(plan)
    report = inspect_ownership(root)
    assert not report.recorded and not report.entries and not report.in_sync


def test_outside_root_doc_symlink_is_not_read(tmp_path: Path) -> None:
    root = generate(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("outside secret sentinel\n")
    (root / "AGENTS.md").unlink()
    (root / "AGENTS.md").symlink_to(outside)
    report = inspect_ownership(root)
    entry = next(e for e in report.entries if e.target == "AGENTS.md")
    assert entry.status == "unreadable" and "outside secret" not in report.to_json()
    assert next(e for e in inspect_docs(root).entries if e.target == "AGENTS.md").status == "unreadable"


def test_structural_unreadable_or_empty_workflow_is_not_content_diffed(tmp_path: Path) -> None:
    root = generate(tmp_path)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_bytes(b"\xff")
    entry = next(e for e in inspect_ownership(root).entries if e.target == ".github/workflows/ci.yml")
    assert entry.status == "unreadable" and not entry.diff
    workflow.write_text("")
    assert (
        next(e for e in inspect_ownership(root).entries if e.target == ".github/workflows/ci.yml").status
        == "structural-gap"
    )


def test_ownership_finalize_failure_prevents_success_or_github(tmp_path: Path, monkeypatch) -> None:
    from unittest.mock import Mock
    from src.utils.errors import ProjectCreationError

    generator = ServiceGenerator("failed", "python", True, {}, root=str(tmp_path))
    write = generator.write_content
    metadata_writes = 0

    def fail_final_metadata(target, content):
        nonlocal metadata_writes
        if target == ".kickstart/scaffold.json":
            metadata_writes += 1
            if metadata_writes == 2:
                return False
        return write(target, content)

    github = Mock()
    monkeypatch.setattr(generator, "write_content", fail_final_metadata)
    monkeypatch.setattr(generator, "create_with_github", github)
    with pytest.raises(ProjectCreationError, match="ownership"):
        generator.create()
    github.assert_not_called()
    assert "ownership" not in json.loads((tmp_path / "failed/.kickstart/scaffold.json").read_text())


def test_cli_human_and_json_modes_report_unrecorded_ownership(tmp_path: Path) -> None:
    root = generate(tmp_path)
    runner = CliRunner()
    human = runner.invoke(app, ["plan", str(root), "--ownership"])
    assert human.exit_code == 0 and "seeds excluded" in human.output
    path, manifest = load(root)
    del manifest["ownership"]
    path.write_text(json.dumps(manifest))
    result = runner.invoke(app, ["plan", str(root), "--ownership", "--json"])
    assert result.exit_code == 1 and not json.loads(result.output)["recorded"]
    human = runner.invoke(app, ["plan", str(root), "--ownership"])
    assert human.exit_code == 1 and "unrecorded" in human.output


def test_cli_bad_target_and_manifest_are_usage_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    bad = runner.invoke(app, ["plan", str(tmp_path / "missing"), "--ownership"])
    assert bad.exit_code == 2 and "ownership plan target" in bad.output
    missing = runner.invoke(app, ["plan", str(tmp_path), "--ownership"])
    assert missing.exit_code == 2 and "cannot inspect" in missing.output


def test_ownership_manifest_outside_root_is_not_read(tmp_path: Path) -> None:
    root = generate(tmp_path)
    path, manifest = load(root)
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(manifest))
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(OwnershipPlanTargetError, match="outside"):
        inspect_ownership(root)


def test_symlink_loop_in_owned_doc_reports_unreadable(tmp_path: Path) -> None:
    root = generate(tmp_path)
    target = root / "AGENTS.md"
    target.unlink()
    target.symlink_to("AGENTS.md")
    report = inspect_ownership(root)
    assert next(e for e in report.entries if e.target == "AGENTS.md").status == "unreadable"
    assert next(e for e in inspect_docs(root).entries if e.target == "AGENTS.md").status == "unreadable"
