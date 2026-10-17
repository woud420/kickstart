"""Manifest migration preserves history and only writes a validated snapshot."""

from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from src.generator.manifest_migration import apply_migration, plan_migration
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from src.utils.errors import ManifestMigrationError


def source(root: Path, version: str = "3.0", **choices) -> tuple[Path, dict]:
    contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        schema_version=version,
        generated_by="kickstart",
        semantics_reference="https://github.com/woud420/kickstart/blob/v0.2.0/docs/scaffold-contract.md",
    )
    contract = replace(contract, **choices)
    manifest = json.loads(contract.manifest_json("old"))
    path = root / ".kickstart/scaffold.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path, manifest


def save(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n")


@pytest.mark.parametrize("version", ["3.0", "3.1", "3.2"])
def test_manifest_only_apply_is_deterministic_and_idempotent(tmp_path: Path, version: str) -> None:
    path, _ = source(tmp_path, version, language="python", framework="minimal")
    (tmp_path / "user.txt").write_text("our code\n")
    (tmp_path / ".kickstart/notes.txt").write_text("our metadata notes\n")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    first = plan_migration(tmp_path)
    assert first.ready and first.to_json() == plan_migration(tmp_path).to_json()
    assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    assert apply_migration(first) == "applied"
    migrated = json.loads(path.read_text())
    assert migrated["schema_version"] == "4.0"
    assert migrated["generated_by"] == "kickstart@0.2.0"
    assert not {"semantics", "docs", "capabilities"} & migrated.keys()
    assert apply_migration(first) == "unchanged"
    assert apply_migration(plan_migration(tmp_path)) == "unchanged"
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert {name for name in after if after[name] != before[name]} == {Path(".kickstart/scaffold.json")}


def test_unknown_provenance_is_explicit_and_never_stamped_with_installed_release(tmp_path: Path) -> None:
    path, manifest = source(tmp_path, language="go")
    del manifest["semantics"]
    del manifest["generated_by"]
    save(path, manifest)
    plan = plan_migration(tmp_path)
    assert plan.ready
    warning = next(d for d in plan.diagnostics if d.code == "unknown-provenance")
    assert not warning.blocking
    assert json.loads(plan.target_json)["generated_by"] == "kickstart"


def test_recorded_version_is_preserved(tmp_path: Path) -> None:
    path, manifest = source(tmp_path, language="go", generated_by="kickstart@0.2.0")
    save(path, manifest)
    assert json.loads(plan_migration(tmp_path).target_json)["generated_by"] == "kickstart@0.2.0"


@pytest.mark.parametrize(
    "kind,package,cli_framework,language,framework",
    [
        ("library", "python", None, "python", None),
        ("library", "rust", None, "rust", None),
        ("cli", "python", "typer", "python", "typer"),
        ("cli", "rust", "clap", "rust", "clap"),
        ("cli", "typescript", "oclif", "typescript", "oclif"),
        ("frontend", None, None, "typescript", "react"),
    ],
)
def test_only_unambiguous_manifest_evidence_recovers_identity(
    tmp_path: Path, kind, package, cli_framework, language, framework
) -> None:
    source(
        tmp_path,
        project_kind=kind,
        artifacts=ScaffoldArtifacts(package=package),
        cli_framework=cli_framework,
        execution_models=("cli" if kind == "cli" else "library" if kind == "library" else "static-site",),
    )
    plan = plan_migration(tmp_path)
    assert plan.ready, plan.diagnostics
    project = json.loads(plan.target_json)["project"]
    assert project["language"] == language
    assert project.get("framework") == framework


def test_application_files_do_not_fill_missing_service_inputs(tmp_path: Path) -> None:
    path, _ = source(tmp_path)
    (tmp_path / "package.json").write_text('{"name":"tooling"}')
    original = path.read_bytes()
    plan = plan_migration(tmp_path)
    assert not plan.ready and plan.target_json is None
    assert plan.diagnostics[0].path == "project.language"
    assert "--language" in plan.diagnostics[0].message
    with pytest.raises(ManifestMigrationError, match="unresolved"):
        apply_migration(plan)
    assert path.read_bytes() == original
    python = plan_migration(tmp_path, language="python")
    assert not python.ready and any(d.path == "project.framework" for d in python.diagnostics)
    assert plan_migration(tmp_path, language="python", framework="minimal").ready


@pytest.mark.parametrize(
    "change",
    [
        "unknown-root",
        "unknown-project",
        "unknown-extension",
        "custom-docs",
        "custom-semantics",
        "producer-conflict",
        "language-conflict",
        "framework-conflict",
        "malformed",
        "unsupported-version",
    ],
)
def test_invalid_or_conflicting_sources_never_change(tmp_path: Path, change: str) -> None:
    path, manifest = source(tmp_path, language="python", framework="minimal")
    kwargs = {}
    if change == "unknown-root":
        manifest["extra"] = "keep"
    elif change == "unknown-project":
        manifest["project"]["custom"] = "keep"
    elif change == "unknown-extension":
        manifest["capabilities"]["other"] = "keep"
    elif change == "custom-docs":
        manifest["docs"]["contracts"] = "custom/contracts/"
    elif change == "custom-semantics":
        manifest["semantics"] = "https://example.invalid/custom-contract"
    elif change == "producer-conflict":
        manifest["generated_by"] = "kickstart@0.1.0"
    elif change == "language-conflict":
        kwargs["language"] = "rust"
    elif change == "framework-conflict":
        kwargs["framework"] = "fastapi"
    elif change == "malformed":
        manifest["project"]["language"] = None
    else:
        manifest["schema_version"] = "3.9"
    save(path, manifest)
    original = path.read_bytes()
    plan = plan_migration(tmp_path, **kwargs)
    assert not plan.ready and plan.diagnostics
    with pytest.raises(ManifestMigrationError):
        apply_migration(plan)
    assert path.read_bytes() == original


def test_changed_source_is_preserved_instead_of_overwritten(tmp_path: Path) -> None:
    path, _ = source(tmp_path, language="go")
    plan = plan_migration(tmp_path)
    edited = path.read_bytes() + b" \n"
    path.write_bytes(edited)
    with pytest.raises(ManifestMigrationError, match="changed since planning"):
        apply_migration(plan)
    assert path.read_bytes() == edited
    assert not list(path.parent.glob(".scaffold-migrate-*"))


def test_mid_apply_source_change_is_detected_before_replace(tmp_path: Path, monkeypatch) -> None:
    path, _ = source(tmp_path, language="go")
    plan = plan_migration(tmp_path)
    fsync = os.fsync
    edited = path.read_bytes() + b" \n"

    def concurrent_edit(fd):
        path.write_bytes(edited)
        fsync(fd)

    monkeypatch.setattr(os, "fsync", concurrent_edit)
    with pytest.raises(ManifestMigrationError, match="changed since planning"):
        apply_migration(plan)
    assert path.read_bytes() == edited
    assert not list(path.parent.glob(".scaffold-migrate-*"))


def test_replace_failure_preserves_original_and_removes_temporary(tmp_path: Path, monkeypatch) -> None:
    path, _ = source(tmp_path, language="go")
    original = path.read_bytes()
    plan = plan_migration(tmp_path)

    def denied(*args):
        raise PermissionError("test denied")

    monkeypatch.setattr(os, "replace", denied)
    with pytest.raises(ManifestMigrationError, match="cannot apply"):
        apply_migration(plan)
    assert path.read_bytes() == original
    assert not list(path.parent.glob(".scaffold-migrate-*"))


def test_source_permissions_survive_atomic_apply(tmp_path: Path) -> None:
    path, _ = source(tmp_path, language="go")
    path.chmod(0o640)
    apply_migration(plan_migration(tmp_path))
    assert path.stat().st_mode & 0o777 == 0o640


@pytest.mark.parametrize("parent_link", [False, True])
def test_symlinked_manifest_or_metadata_directory_is_refused(tmp_path: Path, parent_link: bool) -> None:
    real = tmp_path / "real"
    real.mkdir()
    path, _ = source(real, language="go")
    root = tmp_path / "linked"
    root.mkdir()
    if parent_link:
        (root / ".kickstart").symlink_to(path.parent, target_is_directory=True)
    else:
        (root / ".kickstart").mkdir()
        (root / ".kickstart/scaffold.json").symlink_to(path)
    original = path.read_bytes()
    with pytest.raises(ManifestMigrationError, match="symlink"):
        plan_migration(root)
    assert path.read_bytes() == original


@pytest.mark.parametrize("content", [b"{invalid", b"[]", b"\xff"])
def test_unparseable_sources_produce_blocking_diagnostics(tmp_path: Path, content: bytes) -> None:
    path, _ = source(tmp_path, language="go")
    path.write_bytes(content)
    plan = plan_migration(tmp_path)
    assert not plan.ready and plan.diagnostics[0].code == "invalid-manifest"
    assert path.read_bytes() == content


@pytest.mark.parametrize("target", ['{"schema_version":"3.2"}', "{invalid", "[]"])
def test_invalid_plan_target_is_refused_at_apply(tmp_path: Path, target: str) -> None:
    path, _ = source(tmp_path, language="go")
    plan = replace(plan_migration(tmp_path), target_json=target)
    original = path.read_bytes()
    with pytest.raises(ManifestMigrationError, match="invalid migration target"):
        apply_migration(plan)
    assert path.read_bytes() == original


def test_reviewed_source_hash_is_enforced(tmp_path: Path) -> None:
    path, _ = source(tmp_path, language="go")
    plan = plan_migration(tmp_path)
    original = path.read_bytes()
    with pytest.raises(ManifestMigrationError, match="reviewed SHA-256"):
        apply_migration(plan, expected_sha256="0" * 64)
    assert path.read_bytes() == original
    assert apply_migration(plan, expected_sha256=plan.source_sha256) == "applied"


def test_missing_system_composition_is_unresolved_not_invented(tmp_path: Path) -> None:
    path, manifest = source(tmp_path, project_kind="system", repo_layout="monorepo")
    del manifest["composition"]
    save(path, manifest)
    plan = plan_migration(tmp_path)
    assert not plan.ready and plan.diagnostics[0].path == "composition"


def test_common_cli_framework_can_recover_language_without_legacy_alias(tmp_path: Path) -> None:
    source(tmp_path, "3.2", project_kind="cli", framework="typer", execution_models=("cli",))
    plan = plan_migration(tmp_path)
    assert plan.ready, plan.diagnostics
    assert json.loads(plan.target_json)["project"]["language"] == "python"
