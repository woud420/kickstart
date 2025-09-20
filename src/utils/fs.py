from pathlib import Path
from typing import Any, Dict, Optional
import logging
from jinja2 import Environment, FileSystemLoader, BaseLoader, DictLoader, Template
from jinja2.exceptions import TemplateError, TemplateNotFound

logger = logging.getLogger(__name__)


class TemplateEngine:
    """High-performance Jinja2 template engine with caching and error handling."""
    
    def __init__(self, template_dirs: Optional[list[Path]] = None):
        """Initialize the template engine.
        
        Args:
            template_dirs: List of directories to search for templates
        """
        self.template_dirs = template_dirs or []
        self._env: Optional[Environment] = None
        self._template_cache: Dict[str, Template] = {}
    
    @property
    def env(self) -> Environment:
        """Lazy-load the Jinja2 environment."""
        if self._env is None:
            if self.template_dirs:
                # Use filesystem loader for template directories
                loader = FileSystemLoader([str(d) for d in self.template_dirs])
            else:
                # Use dict loader for string templates
                loader = DictLoader({})
            
            self._env = Environment(
                loader=loader,
                autoescape=False,  # We're not generating HTML
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True
            )

            # Add custom filters
            self._env.filters['classname'] = self._to_class_name
        return self._env

    def _to_class_name(self, value: str) -> str:
        """Convert a service name to a valid Python class name.

        Removes hyphens, underscores, and other invalid characters,
        then converts to PascalCase.

        Args:
            value: Service name to convert

        Returns:
            Valid Python class name
        """
        import re
        # Remove invalid characters and split on word boundaries
        clean_name = re.sub(r'[^a-zA-Z0-9]', ' ', str(value))
        # Split into words and capitalize each
        words = [word.capitalize() for word in clean_name.split() if word]
        # Join words together
        return ''.join(words) if words else 'Service'
    
    def render_template(self, template_path: Path | str, variables: Dict[str, Any]) -> str:
        """Render a template file with the given variables.
        
        Args:
            template_path: Path to template file
            variables: Variables to pass to template
            
        Returns:
            Rendered template content
            
        Raises:
            TemplateError: If template rendering fails
            FileNotFoundError: If template file is not found
        """
        try:
            if isinstance(template_path, Path):
                # Read template file directly
                template_content = template_path.read_text(encoding='utf-8')
                template = self.env.from_string(template_content)
            else:
                # Load template by name from template directories
                template = self.env.get_template(template_path)
            
            return template.render(**variables)
            
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_path}")
            raise FileNotFoundError(f"Template not found: {template_path}") from e
        except TemplateError as e:
            logger.error(f"Template rendering error in {template_path}: {e}")
            raise TemplateError(f"Template rendering failed: {e}") from e
        except UnicodeDecodeError as e:
            logger.error(f"Template encoding error in {template_path}: {e}")
            raise TemplateError(f"Template encoding error: {e}") from e
    
    def render_string(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render a template string with the given variables.
        
        Args:
            template_content: Template content as string
            variables: Variables to pass to template
            
        Returns:
            Rendered template content
            
        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.from_string(template_content)
            return template.render(**variables)
        except TemplateError as e:
            logger.error(f"String template rendering error: {e}")
            raise TemplateError(f"String template rendering failed: {e}") from e


# Global template engine instance
_template_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get the global template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


def write_file(path: Path, template: Path | str, **vars: Any) -> None:
    """Write a template file to the specified path with variable substitution.

    This function supports both Jinja2 templating (recommended) and legacy
    placeholder replacement for backward compatibility.

    Args:
        path: Target file path
        template: Either a Path to a template file or template content as string
        **vars: Template variables

    Raises:
        OSError: If file cannot be written
        TemplateError: If template rendering fails
    """
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(template, Path):
            # Template file path
            try:
                # Set up template engine with correct template directories for inheritance
                template_base_dir = _find_template_base_dir(template)
                engine = TemplateEngine([template_base_dir])

                # Get relative template path for Jinja2
                relative_path = template.relative_to(template_base_dir)
                content = engine.render_template(str(relative_path), vars)
                logger.debug(f"Successfully rendered Jinja2 template: {template}")
            except (TemplateError, FileNotFoundError) as e:
                # Fallback to legacy placeholder replacement
                logger.warning(f"Jinja2 templating failed for {template}, falling back to legacy: {e}")
                content = template.read_text(encoding='utf-8')
                content = _legacy_replace(content, vars)
        else:
            # Template content as string
            try:
                # Try Jinja2 templating first
                engine = get_template_engine()
                content = engine.render_string(template, vars)
                logger.debug("Successfully rendered Jinja2 string template")
            except TemplateError as e:
                # Fallback to legacy placeholder replacement
                logger.warning(f"Jinja2 string templating failed, falling back to legacy: {e}")
                content = _legacy_replace(template, vars)

        # Write the rendered content
        path.write_text(content, encoding='utf-8')
        logger.debug(f"Successfully wrote file: {path}")

    except OSError as e:
        logger.error(f"Failed to write file {path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing file {path}: {e}")
        raise


def _find_template_base_dir(template_path: Path) -> Path:
    """Find the base template directory for Jinja2 inheritance.

    Args:
        template_path: Path to the template file

    Returns:
        Base directory containing the templates directory structure
    """
    # Look for the 'templates' directory in the path
    current = template_path.parent
    while current != current.parent:  # Not root directory
        if current.name == 'templates':
            return current
        current = current.parent

    # Fallback to the directory containing the template
    return template_path.parent


def _legacy_replace(content: str, variables: Dict[str, Any]) -> str:
    """Legacy placeholder replacement for backward compatibility.
    
    Replaces placeholders in the format {{VARIABLE_NAME}} with values.
    
    Args:
        content: Template content
        variables: Variables to replace
        
    Returns:
        Content with placeholders replaced
    """
    for key, value in variables.items():
        # Support both uppercase and original case
        content = content.replace(f"{{{{{key.upper()}}}}}", str(value))
        content = content.replace(f"{{{{{key}}}}}", str(value))
    return content

