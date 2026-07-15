"""Read-only docs plan: per-scenario statuses and manifest round-trips."""

import json
from pathlib import Path

import pytest

from src.generator.docs_plan import DocsPlanTargetError, inspect_docs
from src.generator.markers import begin_marker, fence
from src.generator.projections import (
    PROFILE_DEFAULT,
    PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER,
    ProjectionProfile,
    scaffold_docs_projections,
)
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from src.utils.errors import ManifestShapeError


def _service_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        artifacts=ScaffoldArtifacts(image="dockerfile"),
    )


def _cli_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="cli",
        execution_models=("cli",),
        runtime_platforms=("local",),
        architecture="modular-cli",
        cli_framework="typer",
        command_root="src/cli/commands",
        entrypoint="src/main.py",
        operation_root="src/operations",
        src_root_files=("main.py",),
    )


def _worker_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="worker",
        execution_models=("cloudflare-worker",),
        runtime_platforms=("cloudflare-workers",),
        artifacts=ScaffoldArtifacts(worker="wrangler"),
        provider_targets=("cloudflare",),
    )


def _system_contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="system",
        execution_models=("container",),
        runtime_platforms=("kubernetes",),
        artifacts=ScaffoldArtifacts(iac="terraform"),
        repo_layout="monorepo",
        workspace_tooling="bun-turbo",
        knowledge_adapter="backstage",
    )


def _write_repo(root: Path, contract: ScaffoldContract, profile: ProjectionProfile = PROFILE_DEFAULT) -> None:
    (root / ".kickstart").mkdir(parents=True, exist_ok=True)
    (root / ".kickstart" / "scaffold.json").write_text(contract.manifest_json("planned"), encoding="utf-8")
    for projection in scaffold_docs_projections(contract, profile):
        path = root / projection.target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(projection.content, encoding="utf-8")
    architecture = root / "docs" / "architecture" / "README.md"
    architecture.parent.mkdir(parents=True, exist_ok=True)
    architecture.write_text(fence("architecture-readme", "# planned Architecture\n"), encoding="utf-8")


def test_fresh_scaffold_is_in_sync(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())

    report = inspect_docs(tmp_path)

    assert report.in_sync
    statuses = {entry.artifact_id: entry.status for entry in report.entries}
    assert statuses["agent-map"] == "in-sync"
    assert statuses["architecture-readme"] == "presence-only"


def test_user_content_outside_fence_stays_in_sync(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\n## Team notes\n\nOurs.\n", encoding="utf-8")

    report = inspect_docs(tmp_path)

    assert report.in_sync


def test_edit_inside_fence_is_content_drift_with_diff(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        agents.read_text(encoding="utf-8").replace("orientation surface", "renamed surface"),
        encoding="utf-8",
    )

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "agent-map")
    assert not report.in_sync
    assert entry.status == "content-drift"
    assert "-" in entry.diff and "renamed surface" in entry.diff


def test_unfenced_file_is_a_structural_fact(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    (tmp_path / "AGENTS.md").write_text("# Agent Map\n\nhand-written\n", encoding="utf-8")

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "agent-map")
    assert entry.status == "unfenced"
    assert entry.diff == ""


def test_missing_managed_file_is_would_create(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    (tmp_path / "docs" / "contracts" / "README.md").unlink()

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "contracts-readme")
    assert entry.status == "would-create"


def test_malformed_markers_fail_closed(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + begin_marker("agent-map") + "\n", encoding="utf-8")

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "agent-map")
    assert entry.status == "malformed-markers"


def test_missing_architecture_readme_is_reported(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    (tmp_path / "docs" / "architecture" / "README.md").unlink()

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "architecture-readme")
    assert entry.status == "would-create"
    assert not report.in_sync


def test_unfenced_architecture_readme_is_not_presence_only(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    (tmp_path / "docs" / "architecture" / "README.md").write_text("# hand-written map\n", encoding="utf-8")

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "architecture-readme")
    assert entry.status == "unfenced"
    assert not report.in_sync


def test_malformed_architecture_fence_is_reported(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())
    (tmp_path / "docs" / "architecture" / "README.md").write_text(
        f"{begin_marker('architecture-readme')}\n# map without an end marker\n", encoding="utf-8"
    )

    report = inspect_docs(tmp_path)

    entry = next(entry for entry in report.entries if entry.artifact_id == "architecture-readme")
    assert entry.status == "malformed-markers"
    assert not report.in_sync


def test_from_manifest_rejects_unsupported_schema_versions(tmp_path: Path) -> None:
    manifest = json.loads(_service_contract().manifest_json("planned"))

    manifest["schema_version"] = "4.0"
    with pytest.raises(ManifestShapeError):
        ScaffoldContract.from_manifest(manifest)

    del manifest["schema_version"]
    with pytest.raises(ManifestShapeError):
        ScaffoldContract.from_manifest(manifest)

    manifest["schema_version"] = "3.1"
    assert ScaffoldContract.from_manifest(manifest).schema_version == "3.1"


def test_worker_repo_matches_either_docs_profile(tmp_path: Path) -> None:
    ts_root = tmp_path / "ts-worker"
    rust_root = tmp_path / "rust-worker"
    ts_root.mkdir()
    rust_root.mkdir()
    _write_repo(ts_root, _worker_contract(), PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER)
    _write_repo(rust_root, _worker_contract(), PROFILE_DEFAULT)

    ts_report = inspect_docs(ts_root)
    rust_report = inspect_docs(rust_root)

    assert ts_report.in_sync
    assert rust_report.in_sync
    ts_agent = next(entry for entry in ts_report.entries if entry.artifact_id == "agent-map")
    rust_agent = next(entry for entry in rust_report.entries if entry.artifact_id == "agent-map")
    assert ts_agent.profile == PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER
    assert rust_agent.profile == PROFILE_DEFAULT


def test_missing_manifest_is_a_target_error(tmp_path: Path) -> None:
    with pytest.raises(DocsPlanTargetError):
        inspect_docs(tmp_path)


def test_invalid_manifest_json_is_a_target_error(tmp_path: Path) -> None:
    (tmp_path / ".kickstart").mkdir(parents=True)
    (tmp_path / ".kickstart" / "scaffold.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(DocsPlanTargetError):
        inspect_docs(tmp_path)


def test_report_json_shape(tmp_path: Path) -> None:
    _write_repo(tmp_path, _service_contract())

    payload = json.loads(inspect_docs(tmp_path).to_json())

    assert payload["in_sync"] is True
    assert {entry["artifact"] for entry in payload["entries"]} == {
        "agent-map",
        "contracts-readme",
        "operations-readme",
        "decisions-readme",
        "architecture-readme",
    }


def test_manifest_round_trip_reproduces_projections() -> None:
    for contract in (_service_contract(), _cli_contract(), _worker_contract(), _system_contract()):
        manifest = json.loads(contract.manifest_json("planned"))

        rebuilt = ScaffoldContract.from_manifest(manifest)

        assert scaffold_docs_projections(rebuilt) == scaffold_docs_projections(contract)
        if contract.project_kind == "worker":
            assert scaffold_docs_projections(
                rebuilt, PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER
            ) == scaffold_docs_projections(contract, PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER)


def test_from_manifest_rejects_bad_shapes() -> None:
    good = json.loads(_service_contract().manifest_json("planned"))

    no_project = {key: value for key, value in good.items() if key != "project"}
    bad_kind = json.loads(json.dumps(good))
    bad_kind["project"]["kind"] = "spaceship"
    bad_models = json.loads(json.dumps(good))
    bad_models["execution"]["models"] = "container"
    bad_schema = json.loads(json.dumps(good))
    bad_schema["schema_version"] = 4
    bad_knowledge = json.loads(json.dumps(good))
    bad_knowledge["knowledge_adapter"] = {"kind": "backstage"}

    for manifest in (no_project, bad_kind, bad_models, bad_schema, bad_knowledge):
        with pytest.raises(ManifestShapeError):
            ScaffoldContract.from_manifest(manifest)
