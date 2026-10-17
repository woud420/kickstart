"""Typed CLI option models."""

from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True)
class CreateCommandOptions:
    """Raw create command options before interactive prompts fill gaps."""

    project_type: str | None
    name: str | None
    root: str | None
    lang: str
    gh: bool
    helm: bool
    database: str | None = None
    cache: str | None = None
    auth: str | None = None
    framework: str | None = None
    cloud: str = "multi"
    knowledge: str = "none"
    runtime: str | None = None
    workspace_tooling: str | None = None


@dataclass(frozen=True)
class CreateOptions:
    """Resolved create command options ready for dispatch."""

    project_type: str
    name: str
    root: str | None
    lang: str
    gh: bool
    helm: bool
    database: str | None = None
    cache: str | None = None
    auth: str | None = None
    framework: str | None = None
    cloud: str = "multi"
    knowledge: str = "none"
    runtime: str | None = None
    workspace_tooling: str | None = None


class ServiceCreateKwargs(TypedDict, total=False):
    """Keyword arguments accepted by service creation."""

    helm: bool
    root: str | None
    database: str
    cache: str
    auth: str
    framework: str
    runtime: str


class SystemCreateKwargs(TypedDict, total=False):
    """Keyword arguments accepted by system creation."""

    helm: bool
    root: str | None
    cloud: str
    knowledge: str
    runtime: str
    workspace_tooling: str


MonorepoCreateKwargs = SystemCreateKwargs
