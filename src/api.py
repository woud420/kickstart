"""Public API for Kickstart generators."""

from typing import Any

from src.generator.service import ServiceGenerator
from src.generator.frontend import FrontendGenerator
from src.generator.lib import LibraryGenerator, CLIGenerator
from src.generator.monorepo import MonorepoGenerator

__all__ = [
    "create_service",
    "create_frontend",
    "create_lib",
    "create_cli",
    "create_monorepo",
]


def create_service(name: str, lang: str, gh: bool, config: dict[str, Any], *, helm: bool = False, root: str | None = None,
                  database: str | None = None, cache: str | None = None, auth: str | None = None, framework: str | None = None) -> None:
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
    """
    generator = ServiceGenerator(name, lang, gh, config, helm, root, database, cache, auth, framework)
    generator.create()


def create_frontend(name: str, gh: bool, config: dict[str, Any], *, root: str | None = None) -> None:
    """Create a frontend application."""
    generator = FrontendGenerator(name, gh, config, root)
    generator.create()


def create_lib(name: str, lang: str, gh: bool, config: dict[str, Any], *, root: str | None = None) -> None:
    """Create a library project."""
    generator = LibraryGenerator(name, lang, gh, config, root)
    generator.create()


def create_cli(name: str, lang: str, gh: bool, config: dict[str, Any], *, root: str | None = None) -> None:
    """Create a CLI application."""
    generator = CLIGenerator(name, lang, gh, config, root)
    generator.create()


def create_monorepo(name: str, gh: bool, config: dict[str, Any], *, helm: bool = False, root: str | None = None) -> None:
    """Create an infrastructure monorepo."""
    generator = MonorepoGenerator(name, gh, config, helm, root)
    generator.create()
