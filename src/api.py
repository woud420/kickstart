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


def create_service(name: str, lang: str, gh: bool, config: dict[str, Any], *, helm: bool = False, root: str | None = None) -> None:
    """Create a backend service project."""
    generator = ServiceGenerator(name, lang, gh, config, helm, root)
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
