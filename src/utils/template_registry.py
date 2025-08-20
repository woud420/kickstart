"""Centralized template registry for managing project templates.

This module provides a registry-based approach to template management,
replacing hardcoded template paths with a configurable, extensible system.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging

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
    variables: Set[str]
    language: Optional[str] = None
    project_type: Optional[str] = None


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
        self._templates: Dict[str, TemplateInfo] = {}
        self._language_templates: Dict[str, Dict[str, TemplateInfo]] = {}
        self._project_templates: Dict[str, Dict[str, TemplateInfo]] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize the registry with default template configurations."""
        # Common templates for all project types
        common_templates = [
            TemplateInfo(
                name="readme",
                path="{language}/README.md.tpl",
                description="Project README with documentation",
                variables={"service_name", "description", "language"}
            ),
            TemplateInfo(
                name="gitignore",
                path="{language}/gitignore.tpl",
                description="Language-specific .gitignore file",
                variables={"service_name"}
            ),
            TemplateInfo(
                name="dockerfile",
                path="{language}/Dockerfile.tpl",
                description="Docker container configuration",
                variables={"service_name", "port"}
            ),
            TemplateInfo(
                name="makefile",
                path="{language}/Makefile.tpl",
                description="Build automation with Make",
                variables={"service_name"}
            ),
        ]
        
        # Python-specific templates
        python_templates = [
            TemplateInfo(
                name="requirements",
                path="python/requirements.txt.tpl",
                description="Python dependencies",
                variables={"service_name"},
                language="python"
            ),
            TemplateInfo(
                name="pyproject",
                path="python/pyproject.toml.tpl",
                description="Python project configuration",
                variables={"service_name", "description"},
                language="python"
            ),
        ]
        
        # Rust-specific templates
        rust_templates = [
            TemplateInfo(
                name="cargo",
                path="rust/Cargo.toml.tpl",
                description="Rust project configuration",
                variables={"service_name", "description"},
                language="rust"
            ),
        ]
        
        # Go-specific templates
        go_templates = [
            TemplateInfo(
                name="gomod",
                path="go/go.mod.tpl",
                description="Go module definition",
                variables={"service_name"},
                language="go"
            ),
        ]
        
        # C++-specific templates
        cpp_templates = [
            TemplateInfo(
                name="cmake",
                path="cpp/CMakeLists.txt.tpl",
                description="CMake build configuration",
                variables={"service_name"},
                language="cpp"
            ),
        ]
        
        # Helm templates
        helm_templates = [
            TemplateInfo(
                name="helm_chart",
                path="monorepo/helm/Chart.yaml",
                description="Helm chart metadata",
                variables={"service_name", "version"},
                project_type="helm"
            ),
            TemplateInfo(
                name="helm_values",
                path="monorepo/helm/values.yaml",
                description="Helm chart default values",
                variables={"service_name"},
                project_type="helm"
            ),
            TemplateInfo(
                name="helm_deployment",
                path="monorepo/helm/deployment.yaml",
                description="Kubernetes deployment template",
                variables={"service_name", "image", "port"},
                project_type="helm"
            ),
        ]
        
        # Register all templates
        all_templates = (
            common_templates + python_templates + rust_templates + 
            go_templates + cpp_templates + helm_templates
        )
        
        for template in all_templates:
            self.register_template(template)
    
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
    
    def get_template(self, name: str, language: Optional[str] = None) -> Optional[TemplateInfo]:
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
    
    def get_templates_for_language(self, language: str) -> Dict[str, TemplateInfo]:
        """Get all templates available for a specific language.
        
        Args:
            language: Programming language
            
        Returns:
            Dictionary of template name to template info
        """
        templates = {}
        
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
    
    def get_templates_for_project_type(self, project_type: str) -> Dict[str, TemplateInfo]:
        """Get all templates available for a specific project type.
        
        Args:
            project_type: Type of project (service, frontend, lib, etc.)
            
        Returns:
            Dictionary of template name to template info
        """
        return self._project_templates.get(project_type, {})
    
    def resolve_template_path(self, template: TemplateInfo, **context) -> Path:
        """Resolve the full filesystem path for a template.
        
        Args:
            template: Template information
            **context: Context variables for path resolution
            
        Returns:
            Full path to template file
        """
        resolved_path = template.path.format(**context)
        return self.base_template_dir / resolved_path
    
    def validate_template_variables(self, template: TemplateInfo, variables: Dict[str, any]) -> List[str]:
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
    
    def get_template_configs_for_service(self, language: str) -> List[Dict[str, str]]:
        """Get standard template configurations for a service project.
        
        Args:
            language: Programming language
            
        Returns:
            List of template configurations (target -> template mappings)
        """
        configs = []
        templates = self.get_templates_for_language(language)
        
        # Standard mappings for service projects
        standard_mappings = {
            "readme": "README.md",
            "gitignore": ".gitignore", 
            "dockerfile": "Dockerfile",
            "makefile": "Makefile",
        }
        
        # Language-specific mappings
        language_mappings = {
            "python": {
                "requirements": "requirements.txt",
                "pyproject": "pyproject.toml",
            },
            "rust": {
                "cargo": "Cargo.toml",
            },
            "go": {
                "gomod": "go.mod",
            },
            "cpp": {
                "cmake": "CMakeLists.txt",
            },
        }
        
        # Add standard templates
        for template_name, target_file in standard_mappings.items():
            if template_name in templates:
                configs.append({
                    "target": target_file,
                    "template": templates[template_name].path
                })
        
        # Add language-specific templates
        if language in language_mappings:
            for template_name, target_file in language_mappings[language].items():
                if template_name in templates:
                    configs.append({
                        "target": target_file,
                        "template": templates[template_name].path
                    })
        
        return configs
    
    def list_available_languages(self) -> List[str]:
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
_registry: Optional[TemplateRegistry] = None


def get_template_registry(base_template_dir: Optional[Path] = None) -> TemplateRegistry:
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