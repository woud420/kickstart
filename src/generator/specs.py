"""Typed input specs for generator construction."""

from dataclasses import dataclass

from src.stack.profile import stack_registry
from src.utils.types import GeneratorConfig


@dataclass(frozen=True)
class ServiceSpec:
    """Validated constructor data for service scaffolds.

    The spec normalizes aliases, but it intentionally does not validate
    compatibility. Generators still validate at creation time so existing
    constructor behavior stays unchanged.
    """

    name: str
    language: str
    gh: bool
    config: GeneratorConfig
    helm: bool = False
    root: str | None = None
    database: str | None = None
    cache: str | None = None
    auth: str | None = None
    framework: str | None = None
    runtime: str = "container"

    @classmethod
    def from_options(
        cls,
        name: str,
        language: str,
        gh: bool,
        config: GeneratorConfig,
        *,
        helm: bool = False,
        root: str | None = None,
        database: str | None = None,
        cache: str | None = None,
        auth: str | None = None,
        framework: str | None = None,
        runtime: str = "container",
    ) -> "ServiceSpec":
        """Create a service spec from public constructor options."""
        return cls(
            name=name,
            language=stack_registry.normalize_language(language),
            gh=gh,
            config=config,
            helm=helm,
            root=root,
            database=database,
            cache=cache,
            auth=auth,
            framework=framework,
            runtime=stack_registry.normalize_service_runtime(runtime),
        )


@dataclass(frozen=True)
class SystemSpec:
    """Validated constructor data for system scaffolds."""

    name: str
    gh: bool
    config: GeneratorConfig
    helm: bool = False
    root: str | None = None
    cloud: str = "multi"
    knowledge: str = "none"
    runtime: str = "kubernetes"

    @classmethod
    def from_options(
        cls,
        name: str,
        gh: bool,
        config: GeneratorConfig,
        *,
        helm: bool = False,
        root: str | None = None,
        cloud: str = "multi",
        knowledge: str = "none",
        runtime: str = "kubernetes",
    ) -> "SystemSpec":
        """Create a system spec from public constructor options."""
        return cls(
            name=name,
            gh=gh,
            config=config,
            helm=helm,
            root=root,
            cloud=stack_registry.normalize_cloud(cloud),
            knowledge=stack_registry.normalize_knowledge(knowledge),
            runtime=stack_registry.normalize_system_runtime(runtime),
        )


MonorepoSpec = SystemSpec


@dataclass(frozen=True)
class FrontendSpec:
    """Constructor data for frontend scaffolds."""

    name: str
    gh: bool
    config: GeneratorConfig
    root: str | None = None


@dataclass(frozen=True)
class LibrarySpec:
    """Constructor data for library scaffolds."""

    name: str
    language: str
    gh: bool
    config: GeneratorConfig
    root: str | None = None


@dataclass(frozen=True)
class CliSpec:
    """Constructor data for CLI scaffolds."""

    name: str
    language: str
    gh: bool
    config: GeneratorConfig
    root: str | None = None
