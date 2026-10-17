"""Catalog export boundaries: identity, scalar encoding and write failures."""

import json
from pathlib import Path
from typing import NoReturn

import pytest
import yaml
from typer.testing import CliRunner

from src.cli.main import app
from src.generator.backstage_export import CATALOG_PATH, BackstageExportError, export_backstage
from src.generator.scaffold_contract import MANIFEST_PATH, ScaffoldContract


def _repo(root: Path, name: str, kind: str = "service") -> None:
    contract = ScaffoldContract(
        schema_version="3.2",
        project_kind="system" if kind == "system" else "service",
        execution_models=("container",),
        runtime_platforms=("local",),
        repo_layout="monorepo" if kind == "system" else "single-project",
    )
    (root / ".kickstart").mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_PATH).write_text(contract.manifest_json(name), encoding="utf-8")


def test_distinct_children_cannot_share_a_catalog_name(tmp_path: Path) -> None:
    _repo(tmp_path, "parent", "system")
    for directory in ("first", "second"):
        _repo(tmp_path / "services" / directory, "api")
    with pytest.raises(BackstageExportError, match="both map to fence id"):
        export_backstage(tmp_path)
    assert not (tmp_path / CATALOG_PATH).exists()


@pytest.mark.parametrize(
    "pattern", ["services/api/.kickstart/scaffold.json", "services/../services/api/.kickstart/scaffold.json"]
)
def test_overlapping_globs_still_export_each_manifest_once(tmp_path: Path, pattern: str) -> None:
    _repo(tmp_path, "parent", "system")
    _repo(tmp_path / "services" / "api", "api")
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["composition"]["child_manifest_globs"].append(pattern)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    export_backstage(tmp_path)

    assert (tmp_path / CATALOG_PATH).read_text().count("# kickstart:begin catalog-child-api") == 1


@pytest.mark.parametrize("special", ["\x01", "\x85", "\u2028", "\u2029", "\t", "\n", '"', "\\", "café"])
def test_child_docs_paths_round_trip_as_yaml_strings(tmp_path: Path, special: str) -> None:
    _repo(tmp_path, "parent", "system")
    directory = "before" + special + "after"
    child = tmp_path / "services" / directory
    _repo(child, "api")
    (child / "docs").mkdir()

    result = export_backstage(tmp_path)
    documents = list(yaml.safe_load_all((tmp_path / CATALOG_PATH).read_text(encoding="utf-8")))

    assert result.issues == ()
    assert documents[2]["metadata"]["annotations"]["backstage.io/techdocs-ref"] == f"dir:./services/{directory}"


@pytest.mark.parametrize("refresh", [False, True])
@pytest.mark.parametrize(
    "error", [PermissionError("read-only catalog"), UnicodeEncodeError("utf-8", "x", 0, 1, "probe")]
)
def test_catalog_write_errors_are_domain_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refresh: bool, error: Exception
) -> None:
    _repo(tmp_path, "demo")
    catalog = tmp_path / CATALOG_PATH
    if refresh:
        export_backstage(tmp_path)
        catalog.write_text(catalog.read_text().replace("  name: demo", "  name: edited"))
    before = catalog.read_bytes() if refresh else None

    def denied(self: Path, data: str, encoding: str) -> NoReturn:
        raise error

    monkeypatch.setattr(Path, "write_text", denied)
    with pytest.raises(BackstageExportError, match="cannot write catalog-info.yaml"):
        export_backstage(tmp_path)
    assert (catalog.read_bytes() if catalog.exists() else None) == before


@pytest.mark.parametrize("refresh", [False, True])
def test_failed_writes_have_cli_diagnostics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, refresh: bool) -> None:
    _repo(tmp_path, "demo")
    if refresh:
        export_backstage(tmp_path)
        catalog = tmp_path / CATALOG_PATH
        catalog.write_text(catalog.read_text().replace("  name: demo", "  name: edited"))

    def denied(self: Path, data: str, encoding: str) -> NoReturn:
        raise PermissionError("read-only catalog")

    monkeypatch.setattr(Path, "write_text", denied)
    result = CliRunner().invoke(app, ["export", "backstage", str(tmp_path)])

    assert result.exit_code == 1
    assert "cannot write catalog-info.yaml" in result.output
    assert isinstance(result.exception, SystemExit)


def test_child_cannot_duplicate_the_root_component(tmp_path: Path) -> None:
    _repo(tmp_path, "api", "system")
    _repo(tmp_path / "services" / "child", "api")

    with pytest.raises(BackstageExportError, match="root Component"):
        export_backstage(tmp_path)
    assert not (tmp_path / CATALOG_PATH).exists()


def test_broad_child_glob_does_not_export_the_root_again(tmp_path: Path) -> None:
    _repo(tmp_path, "parent", "system")
    _repo(tmp_path / "services" / "api", "api")
    manifest_path = tmp_path / MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text())
    manifest["composition"]["child_manifest_globs"] = ["**/.kickstart/scaffold.json"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    export_backstage(tmp_path)
    catalog = tmp_path / CATALOG_PATH
    before = catalog.read_bytes()
    documents = list(yaml.safe_load_all(before))

    assert [(d["kind"], d["metadata"]["name"]) for d in documents] == [
        ("Component", "parent"),
        ("System", "parent"),
        ("Component", "api"),
    ]
    assert export_backstage(tmp_path).action == "unchanged"
    assert catalog.read_bytes() == before


def test_symlink_aliases_export_one_child_with_its_original_docs_ref(tmp_path: Path) -> None:
    _repo(tmp_path, "parent", "system")
    child = tmp_path / "services" / "api"
    _repo(child, "api")
    (child / "docs").mkdir()
    (tmp_path / "services" / "a-alias").symlink_to("api", target_is_directory=True)

    export_backstage(tmp_path)
    documents = list(yaml.safe_load_all((tmp_path / CATALOG_PATH).read_text()))

    assert len(documents) == 3
    assert documents[2]["metadata"]["annotations"]["backstage.io/techdocs-ref"] == "dir:./services/a-alias"


@pytest.mark.parametrize("error", [OSError("inaccessible child"), RuntimeError("symlink loop")])
def test_unresolvable_child_manifest_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    _repo(tmp_path, "parent", "system")
    child = tmp_path / "services" / "api"
    _repo(child, "api")
    original = Path.resolve

    def unavailable(self: Path, strict: bool = False) -> Path:
        if self == child / MANIFEST_PATH:
            raise error
        return original(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", unavailable)

    export_backstage(tmp_path)
    documents = list(yaml.safe_load_all((tmp_path / CATALOG_PATH).read_text()))

    assert len(documents) == 2
