from pathlib import Path
from typing import Any, Callable
import logging
from src.utils.fs import write_file
from src.utils.logger import success, warn
from src.utils.template_registry import get_template_registry, TemplateRegistry
from src.utils.error_handling import (
    ErrorCollector, batch_operation_wrapper, handle_file_operations,
    handle_template_operations, safe_operation_context,
    ensure_directory_exists, TemplateError
)

logger = logging.getLogger(__name__)

class BaseGenerator:
    """Base class for all project generators.
    
    Provides common functionality for creating projects including directory
    creation, template rendering, error handling, and project structure setup.
    
    Attributes:
        name: Name of the project being created
        config: Configuration dictionary with user preferences
        project: Path to the project directory
        template_dir: Path to the template directory
        template_registry: Registry for managing templates
    """
    
    name: str
    config: dict[str, Any]
    project: Path
    template_dir: Path
    template_registry: TemplateRegistry
    
    def __init__(self, name: str, config: dict[str, Any], root: str | None = None) -> None:
        """Initialize the base generator.
        
        Args:
            name: Name of the project to create
            config: Configuration dictionary with user preferences
            root: Root directory for project creation (optional)
        """
        self.name = name
        self.config = config
        self.project = Path(root) / name if root else Path(name)
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_registry = get_template_registry(self.template_dir)

    def create_project(self) -> bool:
        """Check if the project directory exists.

        Return ``True`` when it doesn't exist; otherwise log a warning and
        return ``False``.
        """
        if self.project.exists():
            warn(f"Directory '{self.project}' already exists.")
            return False
        return True

    def create_directories(self, directories: list[str]) -> bool:
        """Create multiple directories under the project root.

        Args:
            directories: List of directory paths relative to project root

        Returns:
            True if all directories were created successfully, False otherwise
        """
        def create_single_directory(directory: str) -> bool:
            """Create a single directory with centralized error handling."""
            try:
                ensure_directory_exists(self.project / directory)
                return True
            except Exception:
                return False

        # Use batch operation wrapper for standardized error collection
        collector = batch_operation_wrapper(
            items=directories,
            operation_func=create_single_directory,
            operation_name="Directory creation",
            item_name_func=lambda d: f"{self.project / d}"
        )

        return not collector.has_errors()

    @handle_template_operations(default_return=False, log_errors=True)
    def write_template(self, target: str, template_path: str, **vars: Any) -> bool:
        """Write a template file to the project.

        Args:
            target: Target file path relative to project root
            template_path: Path to template file
            **vars: Template variables

        Returns:
            True if file was written successfully, False otherwise
        """
        resolved_template_path: Path | str
        if isinstance(template_path, str) and not Path(template_path).is_absolute():
            resolved_template_path = self.template_dir / template_path
        else:
            resolved_template_path = template_path

        # Check if template exists
        if isinstance(resolved_template_path, Path) and not resolved_template_path.exists():
            raise TemplateError(f"Template file not found: {template_path}")

        write_file(self.project / target, resolved_template_path, service_name=self.name, **vars)
        logger.debug(f"Successfully wrote template {template_path} to {target}")
        return True

    @handle_file_operations(default_return=False, log_errors=True)
    def write_content(self, target: str, content: str) -> bool:
        """Write direct content to a file in the project.

        Args:
            target: Target file path relative to project root
            content: Content to write to the file

        Returns:
            True if file was written successfully, False otherwise
        """
        write_file(self.project / target, content)
        logger.debug(f"Successfully wrote content to {target}")
        return True

    def log_success(self, message: str) -> None:
        """Log a success message."""
        success(message)

    def get_common_vars(self) -> dict[str, str]:
        """Get common template variables."""
        return {"service_name": self.name}

    def init_basic_structure(self, dirs: list[str]) -> bool:
        """Create the base directory structure for a new project.
        
        Args:
            dirs: List of directories to create
            
        Returns:
            True if all directories were created successfully, False otherwise
        """
        return self.create_directories(dirs)

    def create_architecture_docs(self, title: str) -> bool:
        """Create the architecture documentation directory and README.
        
        Args:
            title: Title for the architecture documentation
            
        Returns:
            True if architecture docs were created successfully, False otherwise
        """
        if not self.create_directories(["architecture"]):
            return False
        return self.write_content("architecture/README.md", f"# {title}\n")

    def write_templates_from_config(self, template_configs: list[dict[str, str]]) -> bool:
        """Write multiple template files from configuration list.

        Args:
            template_configs: List of dicts with 'target' and 'template' keys

        Returns:
            True if all templates were written successfully, False otherwise
        """
        def write_single_template(config: dict[str, str]) -> bool:
            """Write a single template with validation."""
            if 'target' not in config or 'template' not in config:
                raise ValueError(f"Invalid template config: missing 'target' or 'template' key: {config}")

            return self.write_template(config['target'], config['template'])

        # Use batch operation wrapper for standardized error collection
        collector = batch_operation_wrapper(
            items=template_configs,
            operation_func=write_single_template,
            operation_name="Template writing",
            item_name_func=lambda c: f"{c.get('target', 'unknown')} (from {c.get('template', 'unknown')})"
        )

        return not collector.has_errors()

    def create_with_github(self, success_message: str, create_repo_fn: Callable[[], Any] | None = None) -> None:
        """Create project and optionally create GitHub repository.
        
        Args:
            success_message: Message to log on successful creation
            create_repo_fn: Function to call for GitHub repo creation
        """
        self.log_success(success_message)
        if create_repo_fn:
            create_repo_fn()

    def execute_create_flow(self, 
                          directories: list[str],
                          template_configs: list[dict[str, str]],
                          architecture_title: str,
                          success_message: str,
                          language_setup_fn: Callable[[], bool] | None = None,
                          additional_setup_fn: Callable[[], bool] | None = None,
                          github_create_fn: Callable[[], Any] | None = None) -> bool:
        """Execute the common create flow for generators.
        
        Args:
            directories: List of directories to create
            template_configs: List of template configurations
            architecture_title: Title for architecture documentation
            success_message: Success message to log
            language_setup_fn: Optional function for language-specific setup
            additional_setup_fn: Optional function for additional setup
            github_create_fn: Optional function for GitHub repo creation
            
        Returns:
            True if project was created successfully, False otherwise
        """
        if not self.create_project():
            return False

        errors = []
        
        # Use error collector for standardized error tracking
        error_collector = ErrorCollector("Project creation")

        # Create project structure
        if not self.init_basic_structure(directories):
            error_collector.add_error("Failed to create directory structure")
        else:
            error_collector.increment_success()
        error_collector.increment_total()

        # Write template files
        if not self.write_templates_from_config(template_configs):
            error_collector.add_error("Failed to write template files")
        else:
            error_collector.increment_success()
        error_collector.increment_total()

        # Create architecture docs
        with safe_operation_context("Architecture documentation creation", log_errors=True):
            if not self.create_architecture_docs(architecture_title):
                error_collector.add_error("Failed to create architecture documentation")
            else:
                error_collector.increment_success()
        error_collector.increment_total()

        # Language-specific setup
        if language_setup_fn:
            with safe_operation_context("Language-specific setup", log_errors=True):
                if not language_setup_fn():
                    error_collector.add_error("Language-specific setup failed")
                else:
                    error_collector.increment_success()
            error_collector.increment_total()

        # Additional setup
        if additional_setup_fn:
            with safe_operation_context("Additional setup", log_errors=True):
                if not additional_setup_fn():
                    error_collector.add_error("Additional setup failed")
                else:
                    error_collector.increment_success()
            error_collector.increment_total()

        errors = error_collector.errors

        # Log results
        if errors:
            warn(f"Project created with errors: {'; '.join(errors)}")
            # Still log success but mention the issues
            logger.warning(f"Project '{self.name}' created with {len(errors)} error(s)")
        
        # Success message and GitHub integration
        with safe_operation_context("GitHub integration", log_errors=True):
            self.create_with_github(success_message, github_create_fn)
            error_collector.increment_success()
        error_collector.increment_total()

        # Final error reporting
        error_collector.log_summary()
        if error_collector.has_errors():
            error_collector.report_failures()
        
        return not error_collector.has_errors()
