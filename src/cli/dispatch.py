"""Project creation dispatch for CLI commands."""

from dataclasses import dataclass
from typing import Protocol, Unpack


from src.cli.options import CreateOptions, ServiceCreateKwargs, SystemCreateKwargs
from src.utils.error_handling import UnsupportedOptionError, UnsupportedProjectTypeError
from src.utils.types import GeneratorConfig


SYSTEM_PROJECT_TYPES = {"system"}
LEGACY_MONOREPO_PROJECT_TYPES = {"mono", "monorepo"}
HELM_PROJECT_TYPES = SYSTEM_PROJECT_TYPES | LEGACY_MONOREPO_PROJECT_TYPES | {"service"}
KNOWN_PROJECT_TYPES = {"service", "frontend", "lib", "cli"} | SYSTEM_PROJECT_TYPES | LEGACY_MONOREPO_PROJECT_TYPES


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
    system: SystemCreator
    monorepo: SystemCreator


def _reject_inapplicable_options(options: CreateOptions) -> None:
    """Refuse options that the selected project type would silently drop."""
    project_type = options.project_type
    system_like = project_type in SYSTEM_PROJECT_TYPES | LEGACY_MONOREPO_PROJECT_TYPES

    if options.helm and project_type not in HELM_PROJECT_TYPES:
        raise UnsupportedOptionError(
            f"--helm only applies to services and systems, not '{project_type}' projects."
        )

    if project_type != "service":
        service_only = {
            "--database": options.database,
            "--cache": options.cache,
            "--auth": options.auth,
            "--framework": options.framework,
        }
        rejected = [flag for flag, value in service_only.items() if value not in (None, "none")]
        if rejected:
            raise UnsupportedOptionError(
                f"{', '.join(rejected)} only applies to services, not '{project_type}' projects."
            )

    if options.runtime is not None and project_type != "service" and not system_like:
        raise UnsupportedOptionError(
            f"--runtime only applies to services and systems, not '{project_type}' projects."
        )

    if not system_like:
        system_only = {
            "--cloud": None if options.cloud == "multi" else options.cloud,
            "--knowledge": None if options.knowledge == "none" else options.knowledge,
            "--workspace-tooling": options.workspace_tooling,
        }
        rejected = [flag for flag, value in system_only.items() if value is not None]
        if rejected:
            raise UnsupportedOptionError(
                f"{', '.join(rejected)} only applies to systems, not '{project_type}' projects."
            )


def dispatch_project_creation(options: CreateOptions, config: GeneratorConfig, creators: ProjectCreators) -> None:
    """Dispatch resolved create options to the appropriate project creator."""
    if options.project_type not in KNOWN_PROJECT_TYPES:
        raise UnsupportedProjectTypeError(
            f"Type '{options.project_type}' not supported. "
            "Use one of: service, frontend, lib, cli, system."
        )

    _reject_inapplicable_options(options)

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
        creators.system(options.name, options.gh, config, **_system_kwargs(options))
        return

    creators.monorepo(options.name, options.gh, config, **_system_kwargs(options))


def _system_kwargs(options: CreateOptions) -> SystemCreateKwargs:
    """Return keyword args common to system-like project creation."""
    system_kwargs: SystemCreateKwargs = {"helm": options.helm, "root": options.root}
    if options.cloud != "multi":
        system_kwargs["cloud"] = options.cloud
    if options.knowledge != "none":
        system_kwargs["knowledge"] = options.knowledge
    if options.runtime is not None:
        system_kwargs["runtime"] = options.runtime
    if options.workspace_tooling is not None:
        system_kwargs["workspace_tooling"] = options.workspace_tooling
    return system_kwargs
