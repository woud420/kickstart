"""Cited external I/O observations, separate from scaffold regeneration state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Literal

from src.utils.errors import KickstartError

SurfaceCategory = Literal["http", "cli", "file", "config", "network", "all"]


class ExternalIOContractError(KickstartError):
    """Raised when an external surface declaration is incomplete or malformed."""


def _text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ExternalIOContractError(f"{label} must be nonempty single-line text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ExternalIOContractError(f"{label} must be valid UTF-8 text") from error


def _choice(value: str, choices: tuple[str, ...], label: str) -> None:
    if value not in choices:
        raise ExternalIOContractError(f"{label} must be one of {', '.join(choices)}")


@dataclass(frozen=True)
class SourceEvidence:
    """A portable repository-relative citation; content verification is a mapper concern."""

    path: str
    start_line: int
    end_line: int | None = None

    def __post_init__(self) -> None:
        _text(self.path, "evidence path")
        path = PurePosixPath(self.path)
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or "\\" in self.path
            or ":" in self.path
            or self.path.endswith("/")
            or path.as_posix() != self.path
        ):
            raise ExternalIOContractError("evidence path must be a normalized root-relative POSIX file path")
        if type(self.start_line) is not int or self.start_line < 1:
            raise ExternalIOContractError("evidence start_line must be a positive integer")
        if self.end_line is not None and (type(self.end_line) is not int or self.end_line < self.start_line):
            raise ExternalIOContractError("evidence end_line must be an integer at or after start_line")


@dataclass(frozen=True)
class HttpSurface:
    method: str
    path: str
    kind: Literal["http"] = field(default="http", init=False)

    def __post_init__(self) -> None:
        _text(self.method, "HTTP method")
        _text(self.path, "HTTP path")
        if not self.path.startswith("/"):
            raise ExternalIOContractError("HTTP path must start with /")


@dataclass(frozen=True)
class CliSurface:
    command: tuple[str, ...]
    option: str | None = None
    kind: Literal["cli"] = field(default="cli", init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.command, tuple) or not self.command:
            raise ExternalIOContractError("CLI command must be a nonempty argv tuple")
        for part in self.command:
            _text(part, "CLI command argument")
        if self.option is not None:
            _text(self.option, "CLI option")
            if not self.option.startswith("-"):
                raise ExternalIOContractError("CLI option must start with -")


@dataclass(frozen=True)
class FileSurface:
    path: str
    access: Literal["read", "write", "read-write"]
    kind: Literal["file"] = field(default="file", init=False)

    def __post_init__(self) -> None:
        _text(self.path, "file surface path")
        _choice(self.access, ("read", "write", "read-write"), "file access")


@dataclass(frozen=True)
class ConfigSurface:
    name: str
    source: Literal["env", "config"]
    required: bool | None = None
    kind: Literal["config"] = field(default="config", init=False)

    def __post_init__(self) -> None:
        _text(self.name, "configuration name")
        _choice(self.source, ("env", "config"), "configuration source")
        if self.required is not None and type(self.required) is not bool:
            raise ExternalIOContractError("configuration required must be true, false or unknown (null)")


@dataclass(frozen=True)
class NetworkSurface:
    protocol: str
    endpoint: str
    direction: Literal["inbound", "outbound"]
    kind: Literal["network"] = field(default="network", init=False)

    def __post_init__(self) -> None:
        _text(self.protocol, "network protocol")
        _text(self.endpoint, "network endpoint")
        _choice(self.direction, ("inbound", "outbound"), "network direction")


type KnownSurface = HttpSurface | CliSurface | FileSurface | ConfigSurface | NetworkSurface


@dataclass(frozen=True)
class SurfaceObservation:
    surface: KnownSurface
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.surface, (HttpSurface, CliSurface, FileSurface, ConfigSurface, NetworkSurface)):
            raise ExternalIOContractError("observation must name a supported surface")
        if (
            not isinstance(self.evidence, tuple)
            or not self.evidence
            or not all(isinstance(e, SourceEvidence) for e in self.evidence)
        ):
            raise ExternalIOContractError(
                "observation requires a nonempty tuple of source citations; use an unknown otherwise"
            )


@dataclass(frozen=True)
class SurfaceUnknown:
    category: SurfaceCategory
    reason: str

    def __post_init__(self) -> None:
        _choice(self.category, ("http", "cli", "file", "config", "network", "all"), "unknown category")
        _text(self.reason, "unknown reason")


@dataclass(frozen=True)
class ExternalIOContract:
    project: str
    surfaces: tuple[SurfaceObservation, ...]
    unknowns: tuple[SurfaceUnknown, ...]
    schema_version: Literal[1] = field(default=1, init=False)
    coverage: Literal["partial"] = field(default="partial", init=False)

    def __post_init__(self) -> None:
        _text(self.project, "project")
        if not isinstance(self.surfaces, tuple) or not all(isinstance(s, SurfaceObservation) for s in self.surfaces):
            raise ExternalIOContractError("surfaces must be an observation tuple")
        if not isinstance(self.unknowns, tuple) or not all(isinstance(u, SurfaceUnknown) for u in self.unknowns):
            raise ExternalIOContractError("unknowns must be an explicit unknown tuple")
        if not self.surfaces and not self.unknowns:
            raise ExternalIOContractError("an empty surface map requires an explicit unknown reason")
