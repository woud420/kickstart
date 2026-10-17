"""Strict version-1 declaration decoding for the external I/O exporter."""

import json
from pathlib import Path
from typing import Literal, NoReturn, cast

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
    SurfaceCategory,
    SurfaceObservation,
    SurfaceUnknown,
)

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type JsonFields = dict[str, JsonValue]


def _unique_fields(pairs: list[tuple[str, JsonValue]]) -> JsonFields:
    fields: JsonFields = {}
    for key, value in pairs:
        if key in fields:
            raise ExternalIOContractError(f"duplicate JSON key {key!r}")
        fields[key] = value
    return fields


def _invalid_constant(value: str) -> NoReturn:
    raise ExternalIOContractError(f"non-JSON number {value!r}")


def _mapping(value: JsonValue, label: str) -> JsonFields:
    if not isinstance(value, dict):
        raise ExternalIOContractError(f"{label} must be a JSON object")
    return value


def _fields(value: JsonValue, label: str, required: tuple[str, ...], optional: tuple[str, ...] = ()) -> JsonFields:
    fields = _mapping(value, label)
    missing = set(required) - fields.keys()
    extra = fields.keys() - set(required) - set(optional)
    if missing:
        raise ExternalIOContractError(f"{label} missing fields: {', '.join(sorted(missing))}")
    if extra:
        raise ExternalIOContractError(f"{label} has unknown fields: {', '.join(repr(k) for k in sorted(extra))}")
    return fields


def _string(value: JsonValue, label: str) -> str:
    if not isinstance(value, str):
        raise ExternalIOContractError(f"{label} must be a string")
    return value


def _integer(value: JsonValue, label: str) -> int:
    if type(value) is not int:
        raise ExternalIOContractError(f"{label} must be an integer")
    return value


def _array(value: JsonValue, label: str) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ExternalIOContractError(f"{label} must be an array")
    return value


def _evidence(value: JsonValue) -> SourceEvidence:
    fields = _fields(value, "evidence", ("path", "start_line"), ("end_line",))
    end = fields.get("end_line")
    return SourceEvidence(
        _string(fields["path"], "evidence path"),
        _integer(fields["start_line"], "evidence start_line"),
        None if end is None else _integer(end, "evidence end_line"),
    )


def _surface(value: JsonValue) -> KnownSurface:
    fields = _mapping(value, "surface")
    kind = _string(fields.get("kind"), "surface kind")
    if kind == "http":
        _fields(fields, "HTTP surface", ("kind", "method", "path"))
        return HttpSurface(_string(fields["method"], "HTTP method"), _string(fields["path"], "HTTP path"))
    if kind == "cli":
        _fields(fields, "CLI surface", ("kind", "command"), ("option",))
        option = fields.get("option")
        return CliSurface(
            tuple(_string(part, "CLI argument") for part in _array(fields["command"], "CLI command")),
            None if option is None else _string(option, "CLI option"),
        )
    if kind == "file":
        _fields(fields, "file surface", ("kind", "path", "access"))
        return FileSurface(
            _string(fields["path"], "file path"),
            cast(Literal["read", "write", "read-write"], _string(fields["access"], "file access")),
        )
    if kind == "config":
        _fields(fields, "config surface", ("kind", "name", "source"), ("required",))
        required = fields.get("required")
        if required is not None and type(required) is not bool:
            raise ExternalIOContractError("configuration required must be a boolean or null")
        return ConfigSurface(
            _string(fields["name"], "configuration name"),
            cast(Literal["env", "config"], _string(fields["source"], "configuration source")),
            required,
        )
    if kind == "network":
        _fields(fields, "network surface", ("kind", "protocol", "endpoint", "direction"))
        return NetworkSurface(
            _string(fields["protocol"], "network protocol"),
            _string(fields["endpoint"], "network endpoint"),
            cast(Literal["inbound", "outbound"], _string(fields["direction"], "network direction")),
        )
    raise ExternalIOContractError(f"unsupported surface kind {kind!r}")


def _observation(value: JsonValue) -> SurfaceObservation:
    fields = _fields(value, "observation", ("surface", "evidence"))
    return SurfaceObservation(
        _surface(fields["surface"]),
        tuple(_evidence(item) for item in _array(fields["evidence"], "observation evidence")),
    )


def _unknown(value: JsonValue) -> SurfaceUnknown:
    fields = _fields(value, "unknown", ("category", "reason"))
    return SurfaceUnknown(
        cast(SurfaceCategory, _string(fields["category"], "unknown category")),
        _string(fields["reason"], "unknown reason"),
    )


def parse_external_io_json(text: str) -> ExternalIOContract:
    """Decode declared data, retaining semantic validation in the typed model."""
    try:
        value: JsonValue = json.loads(text, object_pairs_hook=_unique_fields, parse_constant=_invalid_constant)
    except (ValueError, RecursionError) as error:
        raise ExternalIOContractError(f"invalid external I/O JSON: {error}") from error
    fields = _fields(value, "contract", ("schema_version", "project", "coverage", "surfaces", "unknowns"))
    if _integer(fields["schema_version"], "schema_version") != 1:
        raise ExternalIOContractError("unsupported external I/O schema_version; expected 1")
    if fields["coverage"] != "partial":
        raise ExternalIOContractError("external I/O coverage must remain partial")
    return ExternalIOContract(
        _string(fields["project"], "project"),
        tuple(_observation(item) for item in _array(fields["surfaces"], "surfaces")),
        tuple(_unknown(item) for item in _array(fields["unknowns"], "unknowns")),
    )


def load_external_io_contract(path: Path) -> ExternalIOContract:
    """Read an explicitly selected declaration without collecting runtime values."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ExternalIOContractError(f"cannot read external I/O declaration: {error}") from error
    return parse_external_io_json(text)
