"""Project creation dispatch for CLI commands."""

from dataclasses import dataclass
from typing import Protocol, Unpack

from rich import print

from src.cli.options import CreateOptions, ServiceCreateKwargs, SystemCreateKwargs
from src.utils.types import GeneratorConfig


SYSTEM_PROJECT_TYPES = {"mono", "monorepo", "system"}


class ServiceCreator(Protocol):
    """Callable that creates a service project."""

    def __call__(
        self,
        name: str,
        lang: str,
        gh: bool,
        config: GeneratorConfig,
        **kwargs: Unpack[ServiceCreateKwargs],
    ) -> None:
        """Create a service."""


class FrontendCreator(Protocol):
    """Callable that creates a frontend project."""

    def __call__(self, name: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
        """Create a frontend."""


class LibraryCreator(Protocol):
    """Callable that creates a library project."""

    def __call__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
        """Create a library."""


class CliCreator(Protocol):
    """Callable that creates a CLI project."""

    def __call__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
        """Create a CLI."""


class SystemCreator(Protocol):
    """Callable that creates a system project."""

    def __call__(
        self,
        name: str,
        gh: bool,
        config: GeneratorConfig,
        **kwargs: Unpack[SystemCreateKwargs],
    ) -> None:
        """Create a system."""


MonorepoCreator = SystemCreator


@dataclass(frozen=True)
class ProjectCreators:
    """Creation functions used by CLI dispatch."""

    service: ServiceCreator
    frontend: FrontendCreator
    lib: LibraryCreator
    cli: CliCreator
    monorepo: SystemCreator


def dispatch_project_creation(options: CreateOptions, config: GeneratorConfig, creators: ProjectCreators) -> None:
    """Dispatch resolved create options to the appropriate project creator."""
    if options.project_type == "service":
        service_kwargs: ServiceCreateKwargs = {"helm": options.helm, "root": options.root}
        if options.database is not None and options.database != "none":
            service_kwargs["database"] = options.database
        if options.cache is not None and options.cache != "none":
            service_kwargs["cache"] = options.cache
        if options.auth is not None and options.auth != "none":
            service_kwargs["auth"] = options.auth
        if options.framework is not None and options.framework != "fastapi":
            service_kwargs["framework"] = options.framework
        if options.runtime is not None:
            service_kwargs["runtime"] = options.runtime

        creators.service(options.name, options.lang, options.gh, config, **service_kwargs)
        return

    if options.project_type == "frontend":
        creators.frontend(options.name, options.gh, config, root=options.root)
        return

    if options.project_type == "lib":
        creators.lib(options.name, options.lang, options.gh, config, root=options.root)
        return

    if options.project_type == "cli":
        creators.cli(options.name, options.lang, options.gh, config, root=options.root)
        return

    if options.project_type in SYSTEM_PROJECT_TYPES:
        system_kwargs: SystemCreateKwargs = {"helm": options.helm, "root": options.root}
        if options.cloud != "multi":
            system_kwargs["cloud"] = options.cloud
        if options.knowledge != "none":
            system_kwargs["knowledge"] = options.knowledge
        if options.runtime is not None:
            system_kwargs["runtime"] = options.runtime

        creators.monorepo(options.name, options.gh, config, **system_kwargs)
        return

    print(f"[bold red]Type '{options.project_type}' not supported.[/]")
