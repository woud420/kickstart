"""Public API for Kickstart generators."""

from src.generator.service import ServiceGenerator
from src.generator.frontend import FrontendGenerator
from src.generator.lib import LibraryGenerator, CLIGenerator
from src.generator.monorepo import MonorepoGenerator
from src.utils.types import GeneratorConfig

__all__ = [
    "create_service",
    "create_frontend",
    "create_lib",
    "create_cli",
    "create_monorepo",
]


def create_service(name: str, lang: str, gh: bool, config: GeneratorConfig, *, helm: bool = False, root: str | None = None,
                  database: str | None = None, cache: str | None = None, auth: str | None = None,
                  framework: str | None = None, runtime: str = "container") -> None:
    """Create a backend service project.

    Args:
        name: Service name
        lang: Programming language
        gh: Create GitHub repository
        config: Configuration dictionary
        helm: Include Helm charts
        root: Root directory
        database: Database extension (postgres, mysql, sqlite)
        cache: Cache extension (redis, memcached)
        auth: Authentication extension (jwt, oauth)
        framework: HTTP framework (None for FastAPI default, minimal for standard library)
        runtime: Runtime target (container or cloudflare-workers)
    """
    generator = ServiceGenerator(
        name,
        lang,
        gh,
        config,
        helm=helm,
        root=root,
        database=database,
        cache=cache,
        auth=auth,
        framework=framework,
        runtime=runtime,
    )
    generator.create()


def create_frontend(name: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
    """Create a frontend application."""
    generator = FrontendGenerator(name, gh, config, root)
    generator.create()


def create_lib(name: str, lang: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
    """Create a library project."""
    generator = LibraryGenerator(name, lang, gh, config, root)
    generator.create()


def create_cli(name: str, lang: str, gh: bool, config: GeneratorConfig, *, root: str | None = None) -> None:
    """Create a CLI application."""
    generator = CLIGenerator(name, lang, gh, config, root)
    generator.create()


def create_monorepo(
    name: str,
    gh: bool,
    config: GeneratorConfig,
    *,
    helm: bool = False,
    root: str | None = None,
    cloud: str = "multi",
    knowledge: str = "both",
    runtime: str = "kubernetes",
) -> None:
    """Create an infrastructure monorepo."""
    generator = MonorepoGenerator(
        name,
        gh,
        config,
        helm=helm,
        root=root,
        cloud=cloud,
        knowledge=knowledge,
        runtime=runtime,
    )
    generator.create()
