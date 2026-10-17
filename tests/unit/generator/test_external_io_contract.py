from dataclasses import FrozenInstanceError
import json

import pytest

from src.generator.external_io_contract import (
    CliSurface,
    ConfigSurface,
    ExternalIOContract,
    ExternalIOContractError,
    FileSurface,
    HttpSurface,
    NetworkSurface,
    SourceEvidence,
    SurfaceObservation,
    SurfaceUnknown,
)
from src.generator.external_io_render import render_external_io_json, render_external_io_markdown


def _contract() -> ExternalIOContract:
    evidence = (SourceEvidence("src/main.py", 2, 4),)
    return ExternalIOContract(
        project="sample",
        surfaces=(
            SurfaceObservation(HttpSurface("GET", "/health"), evidence),
            SurfaceObservation(CliSurface(("sample", "serve"), "--port"), evidence),
            SurfaceObservation(FileSurface("/var/data/input.json", "read"), evidence),
            SurfaceObservation(ConfigSurface("DATABASE_URL", "env", True), evidence),
            SurfaceObservation(NetworkSurface("tcp", "db.example.invalid:5432", "outbound"), evidence),
        ),
        unknowns=(SurfaceUnknown("http", "Authentication has not been inspected"),),
    )


def test_formats_share_versioned_observations_evidence_and_unknowns(monkeypatch) -> None:
    contract = _contract()
    monkeypatch.setenv("DATABASE_URL", "runtime-value-must-not-be-exported")
    encoded = render_external_io_json(contract)
    data = json.loads(encoded)
    markdown = render_external_io_markdown(contract)

    assert data["schema_version"] == 1 and data["coverage"] == "partial"
    assert {row["surface"]["kind"] for row in data["surfaces"]} == {"http", "cli", "file", "config", "network"}
    assert all(row["evidence"] == [{"path": "src/main.py", "start_line": 2, "end_line": 4}] for row in data["surfaces"])
    assert data["unknowns"] == [{"category": "http", "reason": "Authentication has not been inspected"}]
    assert "src/main.py:2-4" in markdown and "Authentication has not been inspected" in markdown
    assert "GET /health" in markdown and "DATABASE_URL" in markdown
    assert "runtime-value-must-not-be-exported" not in encoded + markdown
    assert render_external_io_json(contract) == encoded
    assert render_external_io_markdown(contract) == markdown
    assert contract == _contract()
    with pytest.raises(FrozenInstanceError):
        contract.project = "changed"


@pytest.mark.parametrize(
    "path",
    [
        "/absolute.py",
        "../outside.py",
        "src/../app.py",
        "C:/app.py",
        "C:app.py",
        "src\\app.py",
        "./app.py",
        "src//app.py",
        "src/",
        "",
        "line\nbreak.py",
    ],
)
def test_source_locations_reject_nonportable_or_escaping_paths(path: str) -> None:
    with pytest.raises(ExternalIOContractError):
        SourceEvidence(path, 1)


@pytest.mark.parametrize("start,end", [(0, None), (-1, None), (True, None), (3, 2), (1, 0), (1, True)])
def test_source_locations_reject_invalid_ranges(start: int, end: int | None) -> None:
    with pytest.raises(ExternalIOContractError):
        SourceEvidence("src/main.py", start, end)


def test_observations_require_citations_and_empty_results_require_unknowns() -> None:
    with pytest.raises(ExternalIOContractError):
        SurfaceObservation(HttpSurface("GET", "/"), ())
    with pytest.raises(ExternalIOContractError):
        ExternalIOContract("sample", (), ())
    unknown = ExternalIOContract("sample", (), (SurfaceUnknown("all", "Source extraction has not run"),))
    data = json.loads(render_external_io_json(unknown))
    assert data["surfaces"] == [] and data["unknowns"][0]["category"] == "all"
    assert "Source extraction has not run" in render_external_io_markdown(unknown)


def test_known_surface_still_emits_explicit_empty_unknowns() -> None:
    value = ExternalIOContract(
        "sample", (SurfaceObservation(HttpSurface("GET", "/"), (SourceEvidence("main.py", 1),)),), ()
    )
    assert json.loads(render_external_io_json(value))["unknowns"] == []
    assert "None recorded" in render_external_io_markdown(value)
    assert "partial" in render_external_io_markdown(value)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: HttpSurface("", "/"),
        lambda: HttpSurface("GET", "health"),
        lambda: CliSurface(()),
        lambda: CliSurface(("app",), "port"),
        lambda: FileSurface("file.txt", "execute"),
        lambda: ConfigSurface("KEY", "runtime"),
        lambda: ConfigSurface("KEY", "env", 1),
        lambda: NetworkSurface("tcp", "host", "both"),
        lambda: SurfaceUnknown("other", "why"),
        lambda: SurfaceUnknown("all", ""),
    ],
)
def test_invalid_surface_declarations_fail_explicitly(factory) -> None:
    with pytest.raises(ExternalIOContractError):
        factory()


def test_markdown_keeps_untrusted_text_inside_literal_code_spans() -> None:
    reason = "Uninspected `label` [link](https://example.invalid) <script>literal</script>"
    contract = ExternalIOContract("sample", (), (SurfaceUnknown("all", reason),))
    markdown = render_external_io_markdown(contract)
    assert f"`` {reason} ``" in markdown


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SurfaceObservation("unsupported", (SourceEvidence("main.py", 1),)),
        lambda: ExternalIOContract("sample", [], (SurfaceUnknown("all", "Uninspected"),)),
        lambda: ExternalIOContract("sample", (), [SurfaceUnknown("all", "Uninspected")]),
    ],
)
def test_mutable_or_untyped_records_do_not_bypass_the_contract(factory) -> None:
    with pytest.raises(ExternalIOContractError):
        factory()
