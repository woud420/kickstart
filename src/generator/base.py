from pathlib import Path
from typing import Any, Dict, List, Callable, Optional
import logging
from src.utils.fs import write_file
from src.utils.logger import success, warn
from src.utils.template_registry import get_template_registry, TemplateRegistry

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
        failed_dirs = []
        for directory in directories:
            try:
                (self.project / directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {self.project / directory}")
            except OSError as e:
                logger.error(f"Failed to create directory '{directory}': {e}")
                failed_dirs.append(directory)
            except Exception as e:
                logger.error(f"Unexpected error creating directory '{directory}': {e}")
                failed_dirs.append(directory)
        
        if failed_dirs:
            warn(f"Failed to create directories: {', '.join(failed_dirs)}")
            return False
        return True

    def write_template(self, target: str, template_path: str, **vars: Any) -> bool:
        """Write a template file to the project.
        
        Args:
            target: Target file path relative to project root
            template_path: Path to template file
            **vars: Template variables
            
        Returns:
            True if file was written successfully, False otherwise
        """
        try:
            resolved_template_path: Path | str
            if isinstance(template_path, str) and not Path(template_path).is_absolute():
                resolved_template_path = self.template_dir / template_path
            else:
                resolved_template_path = template_path
            
            # Check if template exists
            if isinstance(resolved_template_path, Path) and not resolved_template_path.exists():
                logger.error(f"Template file not found: {resolved_template_path}")
                warn(f"Template file not found: {template_path}")
                return False
            
            write_file(self.project / target, resolved_template_path, service_name=self.name, **vars)
            logger.debug(f"Successfully wrote template {template_path} to {target}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Template file not found when writing '{target}': {e}")
            warn(f"Template file not found: {template_path}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied when writing '{target}': {e}")
            warn(f"Permission denied writing file: {target}")
            return False
        except OSError as e:
            logger.error(f"OS error when writing '{target}': {e}")
            warn(f"Failed to write file '{target}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error writing template '{target}': {e}")
            warn(f"Unexpected error writing file '{target}': {e}")
            return False

    def write_content(self, target: str, content: str) -> bool:
        """Write direct content to a file in the project.
        
        Args:
            target: Target file path relative to project root
            content: Content to write to the file
            
        Returns:
            True if file was written successfully, False otherwise
        """
        try:
            write_file(self.project / target, content)
            logger.debug(f"Successfully wrote content to {target}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied when writing '{target}': {e}")
            warn(f"Permission denied writing file: {target}")
            return False
        except OSError as e:
            logger.error(f"OS error when writing '{target}': {e}")
            warn(f"Failed to write file '{target}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error writing content to '{target}': {e}")
            warn(f"Unexpected error writing file '{target}': {e}")
            return False

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
        success_count = 0
        failed_templates = []
        
        for config in template_configs:
            try:
                if 'target' not in config or 'template' not in config:
                    logger.error(f"Invalid template config: missing 'target' or 'template' key: {config}")
                    failed_templates.append(str(config))
                    continue
                    
                if self.write_template(config['target'], config['template']):
                    success_count += 1
                else:
                    failed_templates.append(f"{config['target']} (from {config['template']})")
            except Exception as e:
                logger.error(f"Error processing template config {config}: {e}")
                failed_templates.append(f"{config.get('target', 'unknown')} (error: {e})")
        
        if failed_templates:
            warn(f"Failed to write {len(failed_templates)} template(s): {', '.join(failed_templates)}")
            
        logger.info(f"Successfully wrote {success_count}/{len(template_configs)} templates")
        return len(failed_templates) == 0

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
        
        # Create project structure
        if not self.init_basic_structure(directories):
            errors.append("Failed to create directory structure")

        # Write template files
        if not self.write_templates_from_config(template_configs):
            errors.append("Failed to write template files")
        
        # Create architecture docs
        try:
            if not self.create_architecture_docs(architecture_title):
                errors.append("Failed to create architecture documentation")
        except Exception as e:
            logger.error(f"Failed to create architecture docs: {e}")
            errors.append("Failed to create architecture documentation")

        # Language-specific setup
        if language_setup_fn:
            try:
                if not language_setup_fn():
                    errors.append("Language-specific setup failed")
            except Exception as e:
                logger.error(f"Language setup function failed: {e}")
                errors.append(f"Language setup error: {e}")

        # Additional setup
        if additional_setup_fn:
            try:
                if not additional_setup_fn():
                    errors.append("Additional setup failed")
            except Exception as e:
                logger.error(f"Additional setup function failed: {e}")
                errors.append(f"Additional setup error: {e}")

        # Log results
        if errors:
            warn(f"Project created with errors: {'; '.join(errors)}")
            # Still log success but mention the issues
            logger.warning(f"Project '{self.name}' created with {len(errors)} error(s)")
        
        # Success message and GitHub integration
        try:
            self.create_with_github(success_message, github_create_fn)
        except Exception as e:
            logger.error(f"GitHub integration failed: {e}")
            errors.append("GitHub repository creation failed")
        
        return len(errors) == 0
