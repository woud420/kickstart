"""Identity reads preserve explicit metadata and reject contradictory shapes."""

import json

import pytest

from src.generator.scaffold_contract import ScaffoldContract
from src.utils.errors import ManifestShapeError


def _manifest() -> dict:
    return json.loads(ScaffoldContract("service", ("container",), ("local",)).manifest_json("api"))


def test_inverse_preserves_explicit_project_identity() -> None:
    manifest = _manifest()
    manifest["project"].update(language="python", framework="minimal")
    rebuilt = ScaffoldContract.from_manifest(manifest)
    assert rebuilt.manifest("api")["project"] == manifest["project"]


@pytest.mark.parametrize("schema", ["3.0", "3.1"])
def test_legacy_identity_stays_unknown(schema: str) -> None:
    manifest = _manifest()
    manifest["schema_version"] = schema
    rebuilt = ScaffoldContract.from_manifest(manifest).manifest("api")
    assert "language" not in rebuilt["project"]
    assert "framework" not in rebuilt["project"]


@pytest.mark.parametrize("key", ["language", "framework"])
@pytest.mark.parametrize("value", [17, {}, [], True])
def test_inverse_rejects_malformed_identity(key: str, value: int | dict | list | bool) -> None:
    manifest = _manifest()
    manifest["project"][key] = value
    with pytest.raises(ManifestShapeError, match=key):
        ScaffoldContract.from_manifest(manifest)


def test_cli_framework_aliases_cannot_disagree() -> None:
    manifest = _manifest()
    manifest["project"].update(kind="cli", language="python", framework="clap", cli_framework="typer")
    with pytest.raises(ManifestShapeError, match="framework"):
        ScaffoldContract.from_manifest(manifest)
