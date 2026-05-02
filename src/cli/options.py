"""Typed CLI option models."""

from dataclasses import dataclass
from typing import TypedDict


ResolvedCreateArgs = tuple[
    str,
    str,
    str | None,
    str,
    bool,
    bool,
    str | None,
    str | None,
    str | None,
    str | None,
    str,
    str,
    str | None,
]


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
    knowledge: str = "both"
    runtime: str | None = None


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
    knowledge: str = "both"
    runtime: str | None = None

    def as_tuple(self) -> ResolvedCreateArgs:
        """Return the legacy tuple shape used by older CLI helper callers."""
        return (
            self.project_type,
            self.name,
            self.root,
            self.lang,
            self.gh,
            self.helm,
            self.database,
            self.cache,
            self.auth,
            self.framework,
            self.cloud,
            self.knowledge,
            self.runtime,
        )


class ServiceCreateKwargs(TypedDict, total=False):
    """Keyword arguments accepted by service creation."""

    helm: bool
    root: str | None
    database: str
    cache: str
    auth: str
    framework: str
    runtime: str


class MonorepoCreateKwargs(TypedDict, total=False):
    """Keyword arguments accepted by monorepo creation."""

    helm: bool
    root: str | None
    cloud: str
    knowledge: str
    runtime: str
