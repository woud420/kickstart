"""Generator provenance remains truthful before and after manifest reads."""

import json

import pytest

from src import __version__
from src.generator.scaffold_contract import ScaffoldContract
from src.utils.errors import ManifestShapeError


def _contract() -> ScaffoldContract:
    return ScaffoldContract(
        project_kind="service",
        execution_models=("container",),
        runtime_platforms=("local",),
    )


def test_new_manifest_records_generator_release() -> None:
    manifest = _contract().manifest("api")
    assert manifest["generated_by"] == f"kickstart@{__version__}"
    assert f"/v{__version__}/" in manifest["semantics"]


@pytest.mark.parametrize("schema_version", ["3.0", "3.1"])
@pytest.mark.parametrize("generator", ["kickstart", "kickstart@0.4.2"])
def test_reading_manifest_preserves_recorded_generator(schema_version: str, generator: str) -> None:
    manifest = json.loads(_contract().manifest_json("api"))
    manifest["schema_version"] = schema_version
    manifest["generated_by"] = generator
    manifest["semantics"] = "https://github.com/woud420/kickstart/blob/v0.4.2/docs/scaffold-contract.md"
    rebuilt = ScaffoldContract.from_manifest(manifest)
    assert rebuilt.manifest("api")["generated_by"] == generator
    assert rebuilt.manifest("api")["semantics"] == manifest["semantics"]


def test_missing_legacy_generator_does_not_claim_current_release() -> None:
    manifest = json.loads(_contract().manifest_json("api"))
    del manifest["generated_by"]
    rebuilt = ScaffoldContract.from_manifest(manifest)
    assert rebuilt.manifest("api")["generated_by"] == "kickstart"


@pytest.mark.parametrize("generator", [None, 42, {}, []])
def test_malformed_generator_is_rejected(generator: None | int | dict[str, str] | list[str]) -> None:
    manifest = json.loads(_contract().manifest_json("api"))
    manifest["generated_by"] = generator
    with pytest.raises(ManifestShapeError, match="generated_by"):
        ScaffoldContract.from_manifest(manifest)
