"""Extension management system using strategy pattern.

This module provides a unified interface for managing service extensions,
eliminating duplication in extension setup patterns across generators.

The ExtensionManager uses a registry pattern to support different extension
types (database, cache, auth) with configuration-driven approach.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
import logging

logger = logging.getLogger(__name__)


class ExtensionConfig:
    """Configuration for a specific extension."""

    def __init__(
        self,
        name: str,
        extension_type: str,
        templates: List[tuple[str, str]],
        requirements_file: str,
        directories: Optional[List[str]] = None
    ) -> None:
        """Initialize extension configuration.

        Args:
            name: Name of the extension (e.g., "postgres", "redis", "jwt")
            extension_type: Type category (e.g., "database", "cache", "auth")
            templates: List of (target_path, template_path) tuples
            requirements_file: Path to requirements template file
            directories: Optional directories to create
        """
        self.name = name
        self.extension_type = extension_type
        self.templates = templates
        self.requirements_file = requirements_file
        self.directories = directories or []


class ExtensionWriter(Protocol):
    """Protocol for objects that can write extension files."""

    def write_template(self, target_path: str, template_path: str) -> None:
        """Write a template file to target path."""
        ...

    def create_directories(self, directories: List[str]) -> None:
        """Create directories."""
        ...

    def write_content(self, target_path: str, content: str) -> None:
        """Write content to target path."""
        ...

    @property
    def template_dir(self) -> Path:
        """Get template directory path."""
        ...


class Extension(ABC):
    """Abstract base class for all extensions."""

    def __init__(self, config: ExtensionConfig) -> None:
        self.config = config

    @abstractmethod
    def apply(self, writer: ExtensionWriter) -> List[str]:
        """Apply the extension using the provided writer.

        Args:
            writer: Object that provides file writing capabilities

        Returns:
            List of requirements to be added
        """
        pass

    def _load_requirements(self, writer: ExtensionWriter) -> List[str]:
        """Load requirements from extension template file.

        Args:
            writer: Object that provides template directory access

        Returns:
            List of requirement strings from the extension template
        """
        requirements_file = writer.template_dir / self.config.requirements_file

        try:
            with open(requirements_file, "r") as f:
                content = f.read()

            # Parse requirements from template, filtering out comments and empty lines
            requirements = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)

            return requirements
        except FileNotFoundError:
            logger.warning(f"Requirements file not found: {requirements_file}")
            return []


class DatabaseExtension(Extension):
    """Database extension implementation."""

    def apply(self, writer: ExtensionWriter) -> List[str]:
        """Apply database extension."""
        # Write template files
        for target_path, template_path in self.config.templates:
            writer.write_template(target_path, template_path)

        # Create directories
        if self.config.directories:
            writer.create_directories(self.config.directories)

        # Load and return requirements
        return self._load_requirements(writer)


class CacheExtension(Extension):
    """Cache extension implementation."""

    def apply(self, writer: ExtensionWriter) -> List[str]:
        """Apply cache extension."""
        # Write template files
        for target_path, template_path in self.config.templates:
            writer.write_template(target_path, template_path)

        # Create directories
        if self.config.directories:
            writer.create_directories(self.config.directories)

        # Load and return requirements
        return self._load_requirements(writer)


class AuthExtension(Extension):
    """Authentication extension implementation."""

    def apply(self, writer: ExtensionWriter) -> List[str]:
        """Apply authentication extension."""
        # Write template files
        for target_path, template_path in self.config.templates:
            writer.write_template(target_path, template_path)

        # Create directories
        if self.config.directories:
            writer.create_directories(self.config.directories)

        # Load and return requirements
        return self._load_requirements(writer)


class ExtensionManager:
    """Manages service extensions using strategy pattern.

    Provides a unified interface for adding extensions to services,
    eliminating duplication across different extension types.
    """

    def __init__(self) -> None:
        """Initialize the extension manager with default configurations."""
        self._extensions: Dict[str, Dict[str, Extension]] = {}
        self._setup_default_extensions()

    def _setup_default_extensions(self) -> None:
        """Setup default extension configurations."""
        # Database extensions
        postgres_config = ExtensionConfig(
            name="postgres",
            extension_type="database",
            templates=[
                ("src/clients/database.py", "python/extensions/database/dao.py.tpl"),
                ("migrations/001_initial.sql", "python/extensions/database/migrations.sql.tpl")
            ],
            requirements_file="python/extensions/database/requirements.txt.tpl",
            directories=["migrations"]
        )
        self._register_extension(DatabaseExtension(postgres_config))

        # Cache extensions
        redis_config = ExtensionConfig(
            name="redis",
            extension_type="cache",
            templates=[
                ("src/clients/cache.py", "python/extensions/cache/redis_client.py.tpl")
            ],
            requirements_file="python/extensions/cache/requirements.txt.tpl"
        )
        self._register_extension(CacheExtension(redis_config))

        # Authentication extensions
        jwt_config = ExtensionConfig(
            name="jwt",
            extension_type="auth",
            templates=[
                ("src/handler/auth.py", "python/extensions/auth/jwt_auth.py.tpl")
            ],
            requirements_file="python/extensions/auth/requirements.txt.tpl"
        )
        self._register_extension(AuthExtension(jwt_config))

    def _register_extension(self, extension: Extension) -> None:
        """Register an extension in the manager.

        Args:
            extension: Extension instance to register
        """
        ext_type = extension.config.extension_type
        if ext_type not in self._extensions:
            self._extensions[ext_type] = {}

        self._extensions[ext_type][extension.config.name] = extension

    def apply_extensions(
        self,
        writer: ExtensionWriter,
        database: Optional[str] = None,
        cache: Optional[str] = None,
        auth: Optional[str] = None
    ) -> tuple[List[str], List[str]]:
        """Apply multiple extensions and return consolidated results.

        Args:
            writer: Object that provides file writing capabilities
            database: Database extension name (e.g., "postgres")
            cache: Cache extension name (e.g., "redis")
            auth: Authentication extension name (e.g., "jwt")

        Returns:
            Tuple of (extensions_added, all_requirements)
        """
        extensions_added = []
        all_requirements = []

        # Apply database extension
        if database and self._has_extension("database", database):
            extension = self._extensions["database"][database]
            requirements = extension.apply(writer)
            extensions_added.append(f"{database.upper()} database")
            all_requirements.extend(requirements)

        # Apply cache extension
        if cache and self._has_extension("cache", cache):
            extension = self._extensions["cache"][cache]
            requirements = extension.apply(writer)
            extensions_added.append(f"{cache.upper()} cache")
            all_requirements.extend(requirements)

        # Apply auth extension
        if auth and self._has_extension("auth", auth):
            extension = self._extensions["auth"][auth]
            requirements = extension.apply(writer)
            extensions_added.append(f"{auth.upper()} authentication")
            all_requirements.extend(requirements)

        return extensions_added, all_requirements

    def _has_extension(self, extension_type: str, name: str) -> bool:
        """Check if an extension exists.

        Args:
            extension_type: Type of extension (database, cache, auth)
            name: Name of the extension

        Returns:
            True if extension exists, False otherwise
        """
        return (
            extension_type in self._extensions
            and name in self._extensions[extension_type]
        )

    def get_supported_extensions(self) -> Dict[str, List[str]]:
        """Get all supported extensions by type.

        Returns:
            Dictionary mapping extension types to lists of supported names
        """
        result = {}
        for ext_type, extensions in self._extensions.items():
            result[ext_type] = list(extensions.keys())
        return result

    def register_custom_extension(self, extension: Extension) -> None:
        """Register a custom extension.

        Args:
            extension: Custom extension to register
        """
        self._register_extension(extension)