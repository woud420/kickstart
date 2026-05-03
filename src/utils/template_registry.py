"""Centralized template registry for managing project templates.

This module provides a registry-based approach to template management,
replacing hardcoded template paths with a configurable, extensible system.
"""

from pathlib import Path
from typing import Mapping
from dataclasses import dataclass
import logging
from src.stack.profile import stack_registry
from src.utils.types import TemplatePathConfig, TemplateValue

logger = logging.getLogger(__name__)


@dataclass
class TemplateInfo:
    """Information about a project template.
    
    Attributes:
        name: Template identifier
        path: Path to template file (relative to template base directory)
        description: Human-readable description
        variables: Set of template variables required
        language: Programming language (optional)
        project_type: Type of project this template is for
    """
    name: str
    path: str
    description: str
    variables: set[str]
    language: str | None = None
    project_type: str | None = None


@dataclass(frozen=True)
class TemplateMetadata:
    """Display metadata for a template registry entry."""

    name: str
    description: str
    variables: set[str]


COMMON_SERVICE_TEMPLATES = (
    TemplateInfo(
        name="readme",
        path="{language}/README.md.tpl",
        description="Project README with documentation",
        variables={"service_name", "description", "language"},
    ),
    TemplateInfo(
        name="gitignore",
        path="{language}/gitignore.tpl",
        description="Language-specific .gitignore file",
        variables={"service_name"},
    ),
    TemplateInfo(
        name="dockerfile",
        path="{language}/Dockerfile.tpl",
        description="Docker container configuration",
        variables={"service_name", "port"},
    ),
    TemplateInfo(
        name="makefile",
        path="{language}/Makefile.tpl",
        description="Build automation with Make",
        variables={"service_name"},
    ),
)

SERVICE_TEMPLATE_METADATA = {
    "requirements.txt": TemplateMetadata("requirements", "Python dependencies", {"service_name"}),
    "pyproject.toml": TemplateMetadata("pyproject", "Python project configuration", {"service_name", "description"}),
    "Cargo.toml": TemplateMetadata("cargo", "Rust project configuration", {"service_name", "description"}),
    "go.mod": TemplateMetadata("gomod", "Go module definition", {"service_name"}),
    "package.json": TemplateMetadata("package", "Bun package manifest", {"service_name"}),
    "tsconfig.json": TemplateMetadata("tsconfig", "TypeScript compiler configuration", {"service_name"}),
    "tsconfig.build.json": TemplateMetadata(
        "tsconfig_build",
        "TypeScript build compiler configuration",
        {"service_name"},
    ),
    "bunfig.toml": TemplateMetadata("bunfig", "Bun configuration", {"service_name"}),
    "CMakeLists.txt": TemplateMetadata("cmake", "CMake build configuration", {"service_name"}),
}

HELM_TEMPLATE_METADATA = {
    "infra/helm/example-service/Chart.yaml": TemplateMetadata(
        "helm_chart",
        "Helm chart metadata",
        {"service_name", "version"},
    ),
    "infra/helm/example-service/values.yaml": TemplateMetadata(
        "helm_values",
        "Helm chart default values",
        {"service_name"},
    ),
    "infra/helm/example-service/templates/deployment.yaml": TemplateMetadata(
        "helm_deployment",
        "Kubernetes deployment template",
        {"service_name", "image", "port"},
    ),
}


class TemplateRegistry:
    """Registry for managing project templates.
    
    Provides centralized access to templates with validation,
    dependency checking, and extensible template resolution.
    """
    
    def __init__(self, base_template_dir: Path):
        """Initialize the template registry.
        
        Args:
            base_template_dir: Base directory containing all templates
        """
        self.base_template_dir = base_template_dir
        self._templates: dict[str, TemplateInfo] = {}
        self._language_templates: dict[str, dict[str, TemplateInfo]] = {}
        self._project_templates: dict[str, dict[str, TemplateInfo]] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize the registry with default template configurations."""
        for template in COMMON_SERVICE_TEMPLATES:
            self.register_template(template)

        self._register_stack_service_templates()
        self._register_stack_helm_templates()

    def _register_stack_service_templates(self) -> None:
        """Register language templates from the stack profile registry."""
        for language, profile in stack_registry.languages.items():
            if "container" not in profile.service_runtimes:
                continue

            selection = stack_registry.service_selection(language, "container")
            for template in selection.templates:
                metadata = SERVICE_TEMPLATE_METADATA.get(template.target)
                if metadata is None:
                    continue

                self.register_template(
                    TemplateInfo(
                        name=metadata.name,
                        path=template.template,
                        description=metadata.description,
                        variables=metadata.variables,
                        language=language,
                    )
                )

    def _register_stack_helm_templates(self) -> None:
        """Register Helm template metadata from the stack profile registry."""
        for template in stack_registry.helm_template_configs():
            metadata = HELM_TEMPLATE_METADATA.get(template.target)
            if metadata is None:
                continue

            self.register_template(
                TemplateInfo(
                    name=metadata.name,
                    path=f"monorepo/{template.template}",
                    description=metadata.description,
                    variables=metadata.variables,
                    project_type="helm",
                )
            )
    
    def register_template(self, template: TemplateInfo) -> None:
        """Register a new template in the registry.
        
        Args:
            template: Template information to register
        """
        self._templates[template.name] = template
        
        if template.language:
            if template.language not in self._language_templates:
                self._language_templates[template.language] = {}
            self._language_templates[template.language][template.name] = template
        
        if template.project_type:
            if template.project_type not in self._project_templates:
                self._project_templates[template.project_type] = {}
            self._project_templates[template.project_type][template.name] = template
    
    def get_template(self, name: str, language: str | None = None) -> TemplateInfo | None:
        """Get template information by name.
        
        Args:
            name: Template name to look up
            language: Programming language context (optional)
            
        Returns:
            Template information if found, None otherwise
        """
        # Try language-specific lookup first
        if language and language in self._language_templates:
            if name in self._language_templates[language]:
                return self._language_templates[language][name]
        
        # Fall back to global lookup
        return self._templates.get(name)
    
    def get_templates_for_language(self, language: str) -> dict[str, TemplateInfo]:
        """Get all templates available for a specific language.
        
        Args:
            language: Programming language
            
        Returns:
            Dictionary of template name to template info
        """
        templates: dict[str, TemplateInfo] = {}
        
        # Add language-specific templates
        if language in self._language_templates:
            templates.update(self._language_templates[language])
        
        # Add common templates that support this language
        for name, template in self._templates.items():
            if template.language is None:  # Common templates
                # Resolve path with language
                resolved_template = TemplateInfo(
                    name=template.name,
                    path=template.path.format(language=language),
                    description=template.description,
                    variables=template.variables,
                    language=language,
                    project_type=template.project_type
                )
                templates[name] = resolved_template
        
        return templates
    
    def get_templates_for_project_type(self, project_type: str) -> dict[str, TemplateInfo]:
        """Get all templates available for a specific project type.
        
        Args:
            project_type: Type of project (service, frontend, lib, etc.)
            
        Returns:
            Dictionary of template name to template info
        """
        return self._project_templates.get(project_type, {})
    
    def resolve_template_path(self, template: TemplateInfo, **context: TemplateValue) -> Path:
        """Resolve the full filesystem path for a template.
        
        Args:
            template: Template information
            **context: Context variables for path resolution
            
        Returns:
            Full path to template file
        """
        resolved_path = template.path.format(**context)
        return self.base_template_dir / resolved_path
    
    def validate_template_variables(self, template: TemplateInfo, variables: Mapping[str, TemplateValue]) -> list[str]:
        """Validate that all required template variables are provided.
        
        Args:
            template: Template information
            variables: Variables provided for rendering
            
        Returns:
            List of missing variable names (empty if all provided)
        """
        provided_vars = set(variables.keys())
        required_vars = template.variables
        missing_vars = required_vars - provided_vars
        return list(missing_vars)
    
    def get_template_configs_for_service(self, language: str) -> list[TemplatePathConfig]:
        """Get standard template configurations for a service project.
        
        Args:
            language: Programming language
            
        Returns:
            List of template configurations (target -> template mappings)
        """
        return stack_registry.service_template_configs(language, "container")
    
    def list_available_languages(self) -> list[str]:
        """Get list of all supported languages.
        
        Returns:
            List of language identifiers
        """
        languages = set(self._language_templates.keys())
        
        # Also check for template directories
        if self.base_template_dir.exists():
            for item in self.base_template_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    languages.add(item.name)
        
        return sorted(list(languages))


# Global registry instance
_registry: TemplateRegistry | None = None


def get_template_registry(base_template_dir: Path | None = None) -> TemplateRegistry:
    """Get the global template registry instance.
    
    Args:
        base_template_dir: Base template directory (only used on first call)
        
    Returns:
        Global template registry instance
    """
    global _registry
    if _registry is None:
        if base_template_dir is None:
            # Default to templates directory relative to this file
            base_template_dir = Path(__file__).parent.parent / "templates"
        _registry = TemplateRegistry(base_template_dir)
    return _registry
