"""Deterministic Backstage export: field classes, idempotence, fail-closed."""

import json
from pathlib import Path
from typing import cast

import pytest

from src.generator.backstage_export import (
    CATALOG_PATH,
    DEFAULT_LIFECYCLE,
    DEFAULT_OWNER,
    BackstageExportError,
    export_backstage,
)
from src.generator.scaffold_contract import (
    MANIFEST_PATH,
    ProjectKind,
    ScaffoldArtifacts,
    ScaffoldContract,
    ScaffoldServiceExtensions,
)


def _write_manifest(root: Path, contract: ScaffoldContract, name: str) -> None:
    (root / ".kickstart").mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_PATH).write_text(contract.manifest_json(name), encoding="utf-8")


def _service_repo(root: Path) -> None:
    contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        artifacts=ScaffoldArtifacts(image="dockerfile"),
        service_extensions=ScaffoldServiceExtensions(database="postgres"),
    )
    _write_manifest(root, contract, "demo-api")
    (root / "docs").mkdir()


def test_fresh_export_derives_component_with_defaults(tmp_path: Path) -> None:
    _service_repo(tmp_path)

    result = export_backstage(tmp_path)
    content = (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")

    assert result.action == "created"
    assert result.issues == ()
    assert content.startswith("# kickstart:begin catalog-derived\n")
    assert "kind: Component" in content
    assert "  name: demo-api" in content
    assert "backstage.io/techdocs-ref: dir:." in content
    assert "    - container\n    - postgres" in content
    assert f"  lifecycle: {DEFAULT_LIFECYCLE}" in content
    assert f"  owner: {DEFAULT_OWNER}" in content
    assert "  type: service" in content


def test_export_is_idempotent(tmp_path: Path) -> None:
    _service_repo(tmp_path)

    export_backstage(tmp_path)
    first = (tmp_path / CATALOG_PATH).read_bytes()
    result = export_backstage(tmp_path)
    second = (tmp_path / CATALOG_PATH).read_bytes()

    assert result.action == "unchanged"
    assert first == second


def test_declared_and_passthrough_survive_reexport(tmp_path: Path) -> None:
    _service_repo(tmp_path)
    export_backstage(tmp_path)
    target = tmp_path / CATALOG_PATH

    edited = target.read_text(encoding="utf-8")
    edited = edited.replace(f"  owner: {DEFAULT_OWNER}", "  owner: group:default/platform-team")
    edited += "  custom/annotation: kept\n"
    # An edit inside the fence must be reverted by the next export.
    edited = edited.replace("  name: demo-api", "  name: hand-renamed")
    target.write_text(edited, encoding="utf-8")

    result = export_backstage(tmp_path)
    content = target.read_text(encoding="utf-8")

    assert result.action == "updated"
    assert "  owner: group:default/platform-team" in content
    assert "  custom/annotation: kept" in content
    assert "  name: demo-api" in content
    assert "hand-renamed" not in content


def test_unfenced_existing_file_is_refused(tmp_path: Path) -> None:
    _service_repo(tmp_path)
    (tmp_path / CATALOG_PATH).write_text("kind: Component\n", encoding="utf-8")

    with pytest.raises(BackstageExportError):
        export_backstage(tmp_path)


def test_missing_manifest_is_an_export_error(tmp_path: Path) -> None:
    with pytest.raises(BackstageExportError):
        export_backstage(tmp_path)


def test_kind_type_mapping(tmp_path: Path) -> None:
    cases = {
        "worker": "service",
        "frontend": "website",
        "library": "library",
        "cli": "tool",
    }
    for kind, expected_type in cases.items():
        root = tmp_path / kind
        root.mkdir()
        contract = ScaffoldContract(
            project_kind=cast(ProjectKind, kind),
            execution_models=("cli",),
            runtime_platforms=("local",),
        )
        _write_manifest(root, contract, f"demo-{kind}")

        export_backstage(root)

        content = (root / CATALOG_PATH).read_text(encoding="utf-8")
        assert f"  type: {expected_type}" in content, kind


def test_system_export_emits_system_and_children(tmp_path: Path) -> None:
    system_contract = ScaffoldContract(
        project_kind="system",
        execution_models=("container",),
        runtime_platforms=("kubernetes",),
        repo_layout="monorepo",
    )
    _write_manifest(tmp_path, system_contract, "demo-sys")
    child_contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )
    child_root = tmp_path / "services" / "api"
    child_root.mkdir(parents=True)
    _write_manifest(child_root, child_contract, "api")

    result = export_backstage(tmp_path)
    content = (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")

    assert result.action == "created"
    assert "kind: System" in content
    assert "# kickstart:begin catalog-child-api" in content
    assert "  system: demo-sys" in content
    assert content.count("---\n") == 2
    # The child's TechDocs source must point at its own subtree, not the root.
    (tmp_path / "services" / "api" / "docs").mkdir()
    refreshed = export_backstage(tmp_path)
    content = (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")
    assert refreshed.action == "updated"
    assert "backstage.io/techdocs-ref: dir:./services/api" in content


def test_child_fences_refresh_and_underscore_names_are_safe(tmp_path: Path) -> None:
    system_contract = ScaffoldContract(
        project_kind="system",
        execution_models=("container",),
        runtime_platforms=("kubernetes",),
        repo_layout="monorepo",
    )
    _write_manifest(tmp_path, system_contract, "demo-sys")
    child_contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )
    child_root = tmp_path / "services" / "data_api"
    child_root.mkdir(parents=True)
    _write_manifest(child_root, child_contract, "data_api")

    export_backstage(tmp_path)
    content = (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")
    assert "# kickstart:begin catalog-child-data-api" in content
    assert "  name: data_api" in content

    # A derived change in the child (new extension tag) refreshes its fence.
    richer_child = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        service_extensions=ScaffoldServiceExtensions(database="postgres"),
    )
    _write_manifest(child_root, richer_child, "data_api")
    result = export_backstage(tmp_path)
    content = (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")
    assert result.action == "updated"
    assert "    - postgres" in content


def test_nameless_child_is_skipped_not_fatal(tmp_path: Path) -> None:
    system_contract = ScaffoldContract(
        project_kind="system",
        execution_models=("container",),
        runtime_platforms=("kubernetes",),
        repo_layout="monorepo",
    )
    _write_manifest(tmp_path, system_contract, "demo-sys")
    broken_child = tmp_path / "services" / "mystery" / ".kickstart"
    broken_child.mkdir(parents=True)
    manifest = json.loads(
        ScaffoldContract(
            project_kind="service", execution_models=("container",), runtime_platforms=("local",)
        ).manifest_json("mystery")
    )
    del manifest["project"]["name"]
    (broken_child / "scaffold.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = export_backstage(tmp_path)

    assert result.action == "created"
    assert "catalog-child" not in (tmp_path / CATALOG_PATH).read_text(encoding="utf-8")


def test_template_owner_default_matches_exporter_constant() -> None:
    template = Path("src/templates/monorepo/catalog-info.yaml").read_text(encoding="utf-8")

    assert DEFAULT_OWNER in template
    assert "group:default/platform" not in template


def test_export_result_reports_missing_required_lines(tmp_path: Path) -> None:
    _service_repo(tmp_path)
    export_backstage(tmp_path)
    target = tmp_path / CATALOG_PATH
    target.write_text(
        target.read_text(encoding="utf-8").replace(f"  owner: {DEFAULT_OWNER}\n", ""), encoding="utf-8"
    )

    result = export_backstage(tmp_path)

    assert any("owner:" in issue and "entity 1" in issue for issue in result.issues)


def test_manifest_name_round_trips_from_generated_manifest(tmp_path: Path) -> None:
    contract = ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )
    _write_manifest(tmp_path, contract, "named-thing")
    manifest = json.loads((tmp_path / MANIFEST_PATH).read_text(encoding="utf-8"))

    assert manifest["project"]["name"] == "named-thing"
