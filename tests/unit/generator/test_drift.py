"""Drift coverage follows persisted ownership and reports structural facts."""

import json
from pathlib import Path

import pytest

from src.generator.adoption import inspect_repo
from src.generator.drift import inspect_drift
from src.generator.service import ServiceGenerator
from src.generator.workflow_check import inspect_workflow
from src.utils.errors import DriftTargetError


@pytest.fixture
def project(tmp_path: Path) -> Path:
    ServiceGenerator("drifted", "python", False, {}, root=str(tmp_path)).create()
    return tmp_path / "drifted"


def entries(root: Path):
    return {entry.target: entry for entry in inspect_drift(root).entries}


def test_missing_changed_and_stale_findings_are_classed(project: Path) -> None:
    agents = project / "AGENTS.md"
    agents.write_text(agents.read_text().replace("orientation surface", "edited managed surface"))
    (project / "docs/architecture/README.md").unlink()
    (project / "Makefile").write_text("build:\n\t@echo customized\n")
    (project / ".github/workflows/ci.yml").write_text("jobs: {custom: {runs-on: ubuntu-latest}}\n")
    by_target = entries(project)
    assert (by_target["AGENTS.md"].artifact_class, by_target["AGENTS.md"].status) == ("scaffold", "changed")
    assert (
        by_target["docs/architecture/README.md"].artifact_class,
        by_target["docs/architecture/README.md"].status,
    ) == ("docs", "missing")
    assert (by_target["Makefile"].artifact_class, by_target["Makefile"].status) == ("artifact", "stale")
    ci = by_target[".github/workflows/ci.yml"]
    assert ci.artifact_class == "ci" and ci.status == "stale" and "standard job 'check'" in ci.detail
    assert not ci.diff and not by_target["Makefile"].diff


def test_seeds_unlisted_paths_and_user_notes_are_never_compared(project: Path, monkeypatch) -> None:
    seed = project / "src/main.py"
    seed.write_bytes(b"\xff")
    agents = project / "AGENTS.md"
    agents.write_text(agents.read_text() + "\nPrivate user note outside the fence\n")
    unlisted = project / ".github/workflows/user.yml"
    unlisted.write_text("private unlisted workflow\n")
    read = Path.read_text

    def guarded(path, *args, **kwargs):
        if path in (seed, unlisted):
            raise AssertionError("excluded contents were read")
        return read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    report = inspect_drift(project)
    assert report.in_sync and report.seeds_excluded > 0
    assert "Private user note" not in report.to_json()
    assert not any(e.target in ("src/main.py", ".github/workflows/user.yml") for e in report.entries)


def test_edited_ownership_index_controls_content_scope(project: Path, monkeypatch) -> None:
    path = project / ".kickstart/scaffold.json"
    manifest = json.loads(path.read_text())
    manifest["ownership"]["AGENTS.md"] = "seed"
    del manifest["ownership"]["docs/contracts/README.md"]
    path.write_text(json.dumps(manifest))
    read = Path.read_text

    def guarded(target, *args, **kwargs):
        if target in (project / "AGENTS.md", project / "docs/contracts/README.md"):
            raise AssertionError("ownership exclusion ignored")
        return read(target, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    assert inspect_drift(project).in_sync


def test_structural_checks_do_not_compare_customized_recipe_or_job_bodies(project: Path) -> None:
    (project / "Makefile").write_text("verify check:\n\t@echo user recipe\n")
    (project / ".github/workflows/ci.yml").write_text("jobs: {check: {steps: [{run: echo human workflow}]}}\n")
    report = inspect_drift(project)
    assert report.in_sync
    assert not any(e.diff for e in report.entries if e.artifact_class in ("artifact", "ci"))


@pytest.mark.parametrize("target", ["AGENTS.md", "Makefile", ".github/workflows/ci.yml"])
def test_outside_root_links_fail_without_disclosing_contents(project: Path, tmp_path: Path, target: str) -> None:
    outside = tmp_path / "outside"
    outside.write_text("outside secret sentinel\n")
    path = project / target
    path.unlink()
    path.symlink_to(outside)
    report = inspect_drift(project)
    assert next(e for e in report.entries if e.target == target).status == "unreadable"
    assert "outside secret sentinel" not in report.to_json()


@pytest.mark.parametrize("target", ["Makefile", ".github/workflows/ci.yml"])
def test_invalid_utf8_is_a_finding(project: Path, target: str) -> None:
    (project / target).write_bytes(b"\xff")
    assert entries(project)[target].status == "unreadable"


def test_unrecorded_ownership_is_explicit_and_not_inferred(project: Path) -> None:
    path = project / ".kickstart/scaffold.json"
    manifest = json.loads(path.read_text())
    del manifest["ownership"]
    path.write_text(json.dumps(manifest))
    report = inspect_drift(project)
    assert not report.recorded and not report.in_sync and not report.entries
    assert "unavailable" in report.payload()["detail"]
    adopted = inspect_repo(project)
    assert adopted.complete and adopted.drift is not None and not adopted.drift.recorded


def test_adoption_reuses_drift_and_does_not_hide_changed_owned_docs(project: Path) -> None:
    agents = project / "AGENTS.md"
    agents.write_text(agents.read_text().replace("orientation surface", "edited managed surface"))
    report = inspect_repo(project)
    assert report.achieved_level == report.claimed_level == "managed"
    assert not report.complete and report.drift is not None and not report.drift.in_sync


@pytest.mark.parametrize(
    "text",
    [
        "jobs: [check]\n",
        "jobs: {custom: {name: 'check:'}}\n",
        "jobs: {check: one, check: {}}\n",
        "jobs: {check: {}}\njobs: {check: {}}\n",
        "jobs: [\n",
        "jobs: {check: {}}\n---\njobs: {check: {}}\n",
        "? [complex, key]\n: value\njobs: {check: {}}\n",
        "jobs: {check: not-a-job-mapping}\n",
        "jobs: {check: {}, custom: not-a-job-mapping}\n",
    ],
)
def test_workflow_structure_is_not_guessed_from_text_fragments(text: str) -> None:
    assert not inspect_workflow(text, ".github/workflows/ci.yml").ok


@pytest.mark.parametrize(
    "target,job",
    [
        (".github/workflows/ci.yml", "check"),
        (".github/workflows/build.yml", "workspace"),
        (".github/workflows/test.yml", "generated-contracts"),
        (".github/workflows/deploy.yml", "plan"),
    ],
)
def test_standard_workflow_job_identities(target: str, job: str) -> None:
    assert inspect_workflow(f"jobs: {{{job}: {{steps: [{{run: customized}}]}}}}\n", target).ok
    assert not inspect_workflow("jobs: {custom: {}}\n", target).ok


def test_workflow_composition_does_not_construct_python_objects(tmp_path: Path) -> None:
    sentinel = tmp_path / "must-not-exist"
    yaml = f"jobs: {{check: !!python/object/apply:pathlib.Path.touch ['{sentinel}']}}\n"
    assert not inspect_workflow(yaml, ".github/workflows/ci.yml").ok
    assert not sentinel.exists()


def test_bad_target_or_manifest_is_a_usage_error(tmp_path: Path) -> None:
    with pytest.raises(DriftTargetError):
        inspect_drift(tmp_path / "missing")
    with pytest.raises(DriftTargetError):
        inspect_drift(tmp_path)


def test_manifest_link_outside_root_is_not_read(project: Path, tmp_path: Path) -> None:
    path = project / ".kickstart/scaffold.json"
    outside = tmp_path / "outside.json"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(DriftTargetError, match="outside"):
        inspect_drift(project)


def test_adoption_accepts_literal_make_target_lists(project: Path) -> None:
    (project / "Makefile").write_text("verify check:\n\t@echo user recipe\n")
    assert inspect_repo(project).complete


def test_adoption_reports_invalid_makefile_encoding_as_a_gap(project: Path) -> None:
    (project / "Makefile").write_bytes(b"\xff")
    report = inspect_repo(project)
    assert not report.complete
    assert any("unreadable Makefile" in status.issue for status in report.artifacts)


@pytest.mark.parametrize("change", ["remove", "outside-link"])
def test_workflow_changes_between_reads_are_findings_not_escaped_reads(
    project: Path, tmp_path: Path, monkeypatch, change: str
) -> None:
    workflow = project / ".github/workflows/ci.yml"
    outside = tmp_path / "outside-workflow.yml"
    outside.write_text("private external workflow sentinel\n")
    read = Path.read_text
    reads = 0

    def changed_after_read(path, *args, **kwargs):
        nonlocal reads
        if path != workflow:
            return read(path, *args, **kwargs)
        reads += 1
        if reads > 1:
            assert change != "outside-link", "workflow followed a new outside-root link"
            return read(path, *args, **kwargs)
        text = read(path, *args, **kwargs)
        workflow.unlink()
        if change == "outside-link":
            workflow.symlink_to(outside)
        return text

    monkeypatch.setattr(Path, "read_text", changed_after_read)
    report = inspect_drift(project)
    assert next(e for e in report.entries if e.target == ".github/workflows/ci.yml").status == "unreadable"
    assert "private external workflow sentinel" not in report.to_json()
