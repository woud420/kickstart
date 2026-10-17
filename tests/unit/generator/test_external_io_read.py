"""Declared external I/O JSON decoding and model compatibility."""

import json
from pathlib import Path

import pytest

from src.generator.external_io_contract import (
    CliSurface,
    ConfigSurface,
    ExternalIOContract,
    ExternalIOContractError,
    FileSurface,
    HttpSurface,
    KnownSurface,
    NetworkSurface,
    SourceEvidence,
    SurfaceObservation,
    SurfaceUnknown,
)
from src.generator.external_io_read import load_external_io_contract, parse_external_io_json
from src.generator.external_io_render import render_external_io_json

VALID = json.dumps(
    {
        "schema_version": 1,
        "coverage": "partial",
        "project": "sample",
        "surfaces": [
            {
                "surface": {"kind": "http", "method": "GET", "path": "/health"},
                "evidence": [{"path": "src/app.py", "start_line": 1, "end_line": 1}],
            }
        ],
        "unknowns": [{"category": "all", "reason": "Other surfaces have not been inspected"}],
    }
)


@pytest.mark.parametrize(
    "surface",
    [
        HttpSurface("GET", "/health"),
        CliSurface(("demo", "serve"), "--port"),
        CliSurface(("demo",)),
        FileSurface("/var/data/cache", "read-write"),
        ConfigSurface("PORT", "env", True),
        ConfigSurface("region", "config", False),
        ConfigSurface("OPTIONAL", "env"),
        NetworkSurface("https", "https://example.test", "outbound"),
    ],
)
def test_every_surface_round_trips_without_new_manifest_state(surface: KnownSurface) -> None:
    contract = ExternalIOContract(
        "sample",
        (SurfaceObservation(surface, (SourceEvidence("src/main.py", 2, 4), SourceEvidence("src/lib.py", 1))),),
        (SurfaceUnknown("all", "Other surfaces are uninspected"),),
    )

    assert parse_external_io_json(render_external_io_json(contract)) == contract


def test_order_and_explicit_unknowns_survive_decoding() -> None:
    contract = ExternalIOContract(
        "sample",
        tuple(SurfaceObservation(HttpSurface("GET", path), (SourceEvidence("app.py", 1),)) for path in ("/z", "/a")),
        (SurfaceUnknown("network", "Not traced"), SurfaceUnknown("cli", "Not inspected")),
    )

    assert parse_external_io_json(render_external_io_json(contract)) == contract


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('"schema_version": 1', '"schema_version": true', "integer"),
        ('"schema_version": 1', '"schema_version": 1.0', "integer"),
        ('"schema_version": 1', '"schema_version": 2', "schema_version"),
        ('"coverage": "partial"', '"coverage": "complete"', "partial"),
        ('"project": "sample"', '"project": 9', "string"),
        ('"project": "sample"', '"project": ""', "nonempty"),
        ('"project": "sample"', '"project": "sample", "extra": null', "unknown fields"),
        ('"kind": "http"', '"kind": "rpc"', "unsupported surface kind"),
        ('"kind": "http"', '"kind": null', "surface kind"),
        ('"kind": "http"', '"kind": "http", "extra": 1', "unknown fields"),
        ('"method": "GET", ', "", "missing fields"),
        ('"path": "/health"', '"path": "health"', "start with /"),
        ('"path": "src/app.py"', '"path": "../outside.py"', "root-relative"),
        ('"path": "src/app.py"', '"path": false', "string"),
        ('"start_line": 1', '"start_line": false', "integer"),
        ('"start_line": 1', '"start_line": 0', "positive"),
        ('"end_line": 1', '"end_line": "1"', "integer"),
        ('"end_line": 1', '"end_line": 0', "at or after"),
        ('"end_line": 1', '"end_line": 1, "value": "untrusted"', "unknown fields"),
        ('"category": "all"', '"category": "rpc"', "unknown category"),
        ('"reason": "Other surfaces have not been inspected"', '"reason": ""', "nonempty"),
        ('"unknowns": [', '"unknowns": {"unused": [', "valid external I/O JSON"),
    ],
)
def test_malformed_declarations_are_rejected(old: str, new: str, message: str) -> None:
    assert old in VALID
    with pytest.raises(ExternalIOContractError, match=message):
        parse_external_io_json(VALID.replace(old, new, 1))


@pytest.mark.parametrize(
    "text",
    [
        "{",
        "null",
        "[]",
        "{}",
        '{"schema_version": 1, "schema_version": 1}',
        '{"outer": {"kind": "http", "kind": "cli"}}',
        '{"value": NaN}',
        '{"value": Infinity}',
        '{"value": -Infinity}',
        "[" * 2000 + "]" * 2000,
    ],
)
def test_invalid_json_or_object_shape_raises_domain_error(text: str) -> None:
    with pytest.raises(ExternalIOContractError):
        parse_external_io_json(text)


def test_arrays_and_observation_shapes_are_required() -> None:
    base = json.loads(VALID)
    variants = [
        {**base, "surfaces": {}},
        {**base, "unknowns": {}},
        {**base, "surfaces": [None]},
        {**base, "unknowns": [None]},
        {**base, "surfaces": [{"surface": None, "evidence": []}]},
        {**base, "surfaces": [{"surface": {"kind": "http", "method": "GET", "path": "/"}, "evidence": []}]},
        {**base, "surfaces": [], "unknowns": []},
    ]
    for value in variants:
        with pytest.raises(ExternalIOContractError):
            parse_external_io_json(json.dumps(value))


@pytest.mark.parametrize(
    "surface",
    [
        {"kind": "cli", "command": "demo"},
        {"kind": "cli", "command": [1]},
        {"kind": "cli", "command": []},
        {"kind": "cli", "command": ["demo"], "option": True},
        {"kind": "file", "path": "cache", "access": "execute"},
        {"kind": "config", "name": "PORT", "source": "env", "required": 1},
        {"kind": "config", "name": "PORT", "source": "secret-store"},
        {"kind": "config", "name": "PORT", "source": "env", "value": "untrusted"},
        {"kind": "network", "protocol": "https", "endpoint": "example.test", "direction": "sideways"},
    ],
)
def test_family_fields_use_existing_model_validation(
    surface: dict[str, str | int | bool | list[str] | list[int]],
) -> None:
    value = json.loads(VALID)
    value["surfaces"][0]["surface"] = surface
    with pytest.raises(ExternalIOContractError):
        parse_external_io_json(json.dumps(value))


@pytest.mark.parametrize(
    "surface",
    [
        {"kind": "cli", "command": ["demo"]},
        {"kind": "config", "name": "PORT", "source": "env"},
    ],
)
def test_optional_fields_may_be_omitted(surface: dict[str, str | list[str]]) -> None:
    value = json.loads(VALID)
    value["surfaces"][0]["surface"] = surface
    del value["surfaces"][0]["evidence"][0]["end_line"]
    contract = parse_external_io_json(json.dumps(value))
    assert contract.surfaces[0].evidence[0].end_line is None


def test_unknown_only_contract_is_explicitly_partial() -> None:
    value = json.loads(VALID)
    value["surfaces"] = []
    contract = parse_external_io_json(json.dumps(value))
    assert contract.coverage == "partial"
    assert contract.unknowns[0].category == "all"


def test_declaration_loader_reports_read_errors(tmp_path: Path) -> None:
    with pytest.raises(ExternalIOContractError, match="cannot read"):
        load_external_io_contract(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\xff")
    with pytest.raises(ExternalIOContractError, match="cannot read"):
        load_external_io_contract(bad)
