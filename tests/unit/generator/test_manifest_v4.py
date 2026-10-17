"""Schema 4.0 reader and compatibility boundaries (ENG-628)."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from src.generator.docs_plan import inspect_docs
from src.generator.projections import PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER, scaffold_docs_projections
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract, ScaffoldServiceExtensions
from src.utils.errors import ManifestShapeError


def service() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
        language="python",
        framework="fastapi",
        schema_version="4.0",
        service_extensions=ScaffoldServiceExtensions(database="postgres"),
    )


def test_v4_round_trip_uses_flat_extensions_and_drops_legacy_constants() -> None:
    manifest = json.loads(service().manifest_json("api"))
    assert manifest["extensions"] == {"database": "postgres"}
    assert not {"semantics", "docs", "capabilities"} & manifest.keys()
    rebuilt = ScaffoldContract.from_manifest(manifest)
    assert json.loads(rebuilt.manifest_json("api")) == manifest


@pytest.mark.parametrize("version", ["3.0", "3.1", "3.2"])
def test_legacy_serialization_stays_available(version: str) -> None:
    contract = replace(service(), schema_version=version)
    manifest = json.loads(contract.manifest_json("api"))
    assert "capabilities" in manifest and "extensions" not in manifest
    assert ScaffoldContract.from_manifest(manifest).schema_version == version


@pytest.mark.parametrize("version", ["2.0", "3.9", "3", "4.1", "4.0.1", "5.0"])
def test_unknown_versions_are_rejected(version: str) -> None:
    manifest = json.loads(service().manifest_json("api"))
    manifest["schema_version"] = version
    with pytest.raises(ManifestShapeError, match="schema_version"):
        ScaffoldContract.from_manifest(manifest)


@pytest.mark.parametrize("field", ["semantics", "docs", "capabilities", "surprise"])
def test_v4_rejects_extra_or_legacy_fields(field: str) -> None:
    manifest = json.loads(service().manifest_json("api"))
    manifest[field] = {}
    with pytest.raises(ManifestShapeError, match=field):
        ScaffoldContract.from_manifest(manifest)


def test_worker_is_a_service_without_changing_lifecycle_or_docs_profile(tmp_path: Path) -> None:
    worker = replace(
        service(),
        project_kind="worker",
        language="typescript",
        framework=None,
        execution_models=("cloudflare-worker",),
        runtime_platforms=("cloudflare-workers",),
        artifacts=ScaffoldArtifacts(worker="wrangler"),
        provider_targets=("cloudflare",),
        service_extensions=ScaffoldServiceExtensions(),
    )
    manifest = json.loads(worker.manifest_json("edge"))
    assert manifest["project"]["kind"] == "service"
    assert manifest["lifecycle"]["deploy"] == "make deploy"
    assert "build" not in manifest["lifecycle"]
    parsed = ScaffoldContract.from_manifest(manifest)
    assert parsed.project_kind == "service" and parsed.is_worker
    (tmp_path / ".kickstart").mkdir()
    (tmp_path / ".kickstart/scaffold.json").write_text(json.dumps(manifest))
    for projection in scaffold_docs_projections(parsed, PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER):
        path = tmp_path / projection.target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(projection.content)
    report = inspect_docs(tmp_path)
    assert all(entry.ok for entry in report.entries if entry.artifact_id != "architecture-readme")
    assert (
        next(e for e in report.entries if e.artifact_id == "contracts-readme").profile
        == PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER
    )


@pytest.mark.parametrize(
    "change", ["missing-language", "system-language", "worker-kind", "mixed-worker", "cli-framework"]
)
def test_v4_rejects_missing_or_conflicting_identity(change: str) -> None:
    manifest = json.loads(service().manifest_json("api"))
    if change == "missing-language":
        del manifest["project"]["language"]
    elif change == "system-language":
        manifest["project"]["kind"] = "system"
    elif change == "worker-kind":
        manifest["project"]["kind"] = "worker"
    elif change == "mixed-worker":
        manifest["execution"]["models"] = ["container", "cloudflare-worker"]
    else:
        manifest["project"].update(kind="cli", framework="typer", cli_framework="clap")
        manifest["execution"]["models"] = ["cli"]
    with pytest.raises(ManifestShapeError):
        ScaffoldContract.from_manifest(manifest)


@pytest.mark.parametrize(
    "kind,language,framework,models,platforms",
    [
        ("service", "python", "minimal", ("container",), ("local",)),
        ("service", "go", None, ("container",), ("local",)),
        ("service", "cpp", None, ("container",), ("local",)),
        ("worker", "rust", None, ("cloudflare-worker",), ("cloudflare-workers",)),
        ("frontend", "typescript", "react", ("static-site",), ("static-host",)),
        ("library", "rust", None, ("library",), ("local",)),
        ("library", "python", None, ("library",), ("local",)),
        ("cli", "python", "typer", ("cli",), ("local",)),
        ("cli", "rust", "clap", ("cli",), ("local",)),
        ("cli", "typescript", "oclif", ("cli",), ("local",)),
        ("system", None, None, ("container",), ("kubernetes",)),
    ],
)
def test_supported_v4_variants_round_trip(kind, language, framework, models, platforms) -> None:
    contract = ScaffoldContract(
        project_kind=kind,
        language=language,
        framework=framework,
        schema_version="4.0",
        execution_models=models,
        runtime_platforms=platforms,
        artifacts=ScaffoldArtifacts(worker="wrangler") if kind == "worker" else ScaffoldArtifacts(),
        provider_targets=("cloudflare",) if kind == "worker" else (),
        repo_layout="monorepo" if kind == "system" else "single-project",
    )
    manifest = json.loads(contract.manifest_json("variant"))
    assert json.loads(ScaffoldContract.from_manifest(manifest).manifest_json("variant")) == manifest


def test_published_schema_matches_typed_source_and_is_valid() -> None:
    from jsonschema import Draft202012Validator
    from src.generator.manifest_schema import manifest_v4_schema, manifest_v4_schema_json

    schema = manifest_v4_schema()
    Draft202012Validator.check_schema(schema)
    root = Path(__file__).resolve().parents[3]
    assert (root / "docs/contracts/scaffold-4.0.schema.json").read_text() == manifest_v4_schema_json()


@pytest.mark.parametrize(
    "path,value",
    [
        (("project", "name"), ""),
        (("project", "extra"), "discarded"),
        (("execution", "models"), "container"),
        (("artifacts", "image"), None),
        (("provider", "targets"), [True]),
        (("extensions", "database"), 42),
        (("lifecycle", "check"), []),
        (("generated_by",), None),
        (("composition",), {}),
        (("schema_version",), []),
    ],
)
def test_schema_and_reader_reject_the_same_malformed_payloads(path, value) -> None:
    from jsonschema import Draft202012Validator
    from src.generator.manifest_schema import manifest_v4_schema

    manifest = json.loads(service().manifest_json("api"))
    target = manifest
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    assert not Draft202012Validator(manifest_v4_schema()).is_valid(manifest)
    with pytest.raises(ManifestShapeError):
        ScaffoldContract.from_manifest(manifest)


def test_v4_system_preserves_recorded_composition() -> None:
    contract = ScaffoldContract(project_kind="system", execution_models=(), runtime_platforms=(), schema_version="4.0")
    manifest = json.loads(contract.manifest_json("system"))
    manifest["composition"]["child_manifest_globs"] = ["services/*/.kickstart/scaffold.json"]
    manifest["composition"]["validation"] = "Read each child before validating."
    assert json.loads(ScaffoldContract.from_manifest(manifest).manifest_json("system")) == manifest


@pytest.mark.parametrize(
    "models,platforms",
    [
        (("cloudflare-worker",), ("cloudflare-workers",)),
        (("container", "cloudflare-worker"), ("kubernetes", "cloudflare-workers")),
    ],
)
def test_system_worker_components_do_not_make_the_root_a_worker(models, platforms) -> None:
    contract = ScaffoldContract(
        project_kind="system",
        execution_models=models,
        runtime_platforms=platforms,
        schema_version="4.0",
        repo_layout="monorepo",
    )
    assert not contract.is_worker
    manifest = json.loads(contract.manifest_json("system"))
    parsed = ScaffoldContract.from_manifest(manifest)
    assert not parsed.is_worker
    assert "workspace" in parsed.contract_subjects
    assert parsed.resolved_lifecycle().deploy is None
    assert json.loads(parsed.manifest_json("system")) == manifest


def test_legacy_manifest_cannot_silently_mix_flat_extensions() -> None:
    manifest = json.loads(replace(service(), schema_version="3.2").manifest_json("api"))
    manifest["extensions"] = {"database": "postgres"}
    with pytest.raises(ManifestShapeError, match="extensions requires schema_version 4.0"):
        ScaffoldContract.from_manifest(manifest)


def test_adoption_surfaces_invalid_v4_as_a_manifest_gap(tmp_path: Path) -> None:
    from src.generator.adoption import inspect_repo

    manifest = json.loads(service().manifest_json("api"))
    manifest["extensions"]["unexpected"] = "ignored"
    path = tmp_path / ".kickstart/scaffold.json"
    path.parent.mkdir()
    path.write_text(json.dumps(manifest))
    original = path.read_bytes()
    report = inspect_repo(tmp_path)
    issue = next(item for item in report.artifacts if item.path == ".kickstart/scaffold.json")
    assert not issue.ok and "unexpected" in issue.issue
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "kind,language,framework,models",
    [
        ("library", "rust", None, ["cloudflare-worker"]),
        ("frontend", "typescript", "react", ["container"]),
        ("cli", "python", "typer", ["static-site"]),
        ("service", "go", None, ["cli"]),
    ],
)
def test_v4_rejects_execution_models_from_another_project_kind(kind, language, framework, models) -> None:
    manifest = json.loads(service().manifest_json("api"))
    manifest["project"].update(kind=kind, language=language)
    if framework is None:
        manifest["project"].pop("framework", None)
    else:
        manifest["project"]["framework"] = framework
    manifest["execution"]["models"] = models
    with pytest.raises(ManifestShapeError, match="models"):
        ScaffoldContract.from_manifest(manifest)
