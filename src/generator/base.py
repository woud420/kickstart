import re
import logging
from collections.abc import Callable, Sequence
from pathlib import Path

from src.generator.file_plan import ContentFile
from src.generator.projections import (
    PROFILE_DEFAULT,
    architecture_readme_projection,
    scaffold_docs_projections,
)
from src.generator.scaffold_contract import ScaffoldContract
from src.generator.template_plan import TemplatePlan, TemplatePlanEntry
from src.stack.toolchain_versions import toolchain_vars
from src.stack.types import TemplateConfig
from src.utils.fs import get_template_engine, write_file
from src.utils.logger import success, warn
from src.utils.template_registry import get_template_registry, TemplateRegistry
from src.utils.types import GeneratorConfig, TemplateValue, TemplateVars
from src.utils.error_handling import (
    ErrorCollector, batch_operation_wrapper, handle_file_operations,
    handle_template_operations, safe_operation_context,
    ensure_directory_exists,
)
from src.utils.errors import InvalidProjectNameError, ProjectCreationError, TemplateError

logger = logging.getLogger(__name__)

# Lowercase letter first, then lowercase letters, digits, dashes, or
# underscores. Rejects path separators (and with them traversal like
# `../evil`), dots, spaces, uppercase, and leading dashes.
PROJECT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
PROJECT_NAME_MAX_LENGTH = 64


def validate_project_name(name: str) -> str:
    """Return the name when valid; raise a specific error otherwise."""
    if len(name) > PROJECT_NAME_MAX_LENGTH:
        raise InvalidProjectNameError(
            f"Project name '{name}' is longer than {PROJECT_NAME_MAX_LENGTH} characters."
        )
    if PROJECT_NAME_PATTERN.fullmatch(name) is None:
        raise InvalidProjectNameError(
            f"Project name '{name}' is not allowed. Use a lowercase name that starts with a letter "
            "and contains only letters, digits, dashes, or underscores (for example: my-api)."
        )
    return name

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
    config: GeneratorConfig
    project: Path
    template_dir: Path
    template_registry: TemplateRegistry
    
    def __init__(self, name: str, config: GeneratorConfig, root: str | None = None) -> None:
        """Initialize the base generator.
        
        Args:
            name: Name of the project to create
            config: Configuration dictionary with user preferences
            root: Root directory for project creation (optional)
        """
        self.name = validate_project_name(name)
        self.config = config
        self.project = Path(root) / name if root else Path(name)
        self.template_dir = Path(__file__).parent.parent / "templates"
        self._templates_root = self.template_dir
        self.template_registry = get_template_registry(self.template_dir)

    def create_project(self) -> bool:
        """Check if the project directory exists.

        Return ``True`` when it doesn't exist; otherwise log a warning and
        return ``False``.
        """
        try:
            if self.project.exists():
                warn(f"Directory '{self.project}' already exists.")
                return False
        except OSError as exc:
            warn(f"Cannot access project directory '{self.project}': {exc}")
            return False
        return True

    def create_directories(self, directories: Sequence[str]) -> bool:
        """Create multiple directories under the project root.

        Args:
            directories: Directory paths relative to project root

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
    def write_template(self, target: str, template_path: str, **vars: TemplateValue) -> bool:
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
            if template_path.startswith("_shared/"):
                resolved_template_path = self._templates_root / template_path
            else:
                resolved_template_path = self.template_dir / template_path
        else:
            resolved_template_path = template_path

        # Check if template exists
        if isinstance(resolved_template_path, Path) and not resolved_template_path.exists():
            raise TemplateError(f"Template file not found: {template_path}")

        template_vars = {
            "service_name": self.name,
            "package_name": self._package_name(),
            **toolchain_vars(),
            **vars,
        }
        write_file(self.project / target, resolved_template_path, **template_vars)
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
        write_file(
            self.project / target,
            content,
            service_name=self.name,
            package_name=self._package_name(),
        )
        logger.debug(f"Successfully wrote content to {target}")
        return True

    def write_content_files(self, files: Sequence[ContentFile]) -> bool:
        """Write multiple direct content files from a typed file plan."""
        success = True
        for file in files:
            if self.write_content(file.target, file.content) is False:
                success = False
        return success

    def write_template_configs(
        self,
        templates: Sequence[TemplateConfig],
        base_vars: TemplateVars | None = None,
    ) -> bool:
        """Write multiple template files from typed template configs."""
        success = True
        for template in templates:
            template_vars = dict(base_vars or {})
            template_vars.update(template.vars)
            if self.write_template(template.target, template.template, **template_vars) is False:
                success = False
        return success

    def write_template_content_files(self, templates: Sequence[TemplateConfig]) -> bool:
        """Write template files through the direct-content path.

        This keeps generated source code in template files while preserving call
        sites that intentionally write rendered source as direct content.
        """
        success = True
        for template in templates:
            template_vars: dict[str, TemplateValue] = {
                "service_name": self.name,
                "package_name": self._package_name(),
                **toolchain_vars(),
            }
            template_vars.update(template.vars)
            base_dir = self._templates_root if template.template.startswith("_shared/") else self.template_dir
            source = (base_dir / template.template).read_text(encoding="utf-8")
            content = get_template_engine().render_string(source, template_vars)
            if self.write_content(template.target, content) is False:
                success = False
        return success

    def _package_name(self) -> str:
        """Return a package-manager-safe name derived from the project name."""
        normalized = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return normalized or "app"

    def log_success(self, message: str) -> None:
        """Log a success message."""
        success(message)

    def get_common_vars(self) -> dict[str, str]:
        """Get common template variables."""
        return {"service_name": self.name}

    def init_basic_structure(self, dirs: Sequence[str]) -> bool:
        """Create the base directory structure for a new project.
        
        Args:
            dirs: Directories to create
            
        Returns:
            True if all directories were created successfully, False otherwise
        """
        return self.create_directories(dirs)

    def create_architecture_docs(
        self,
        title: str,
        directories: Sequence[str] = (),
        contract: ScaffoldContract | None = None,
    ) -> bool:
        """Create the architecture README with a human-oriented module map.

        Args:
            title: Title for the architecture documentation
            directories: Generated directory layout to describe
            contract: Scaffold contract supplying capabilities and entrypoint

        Returns:
            True if architecture docs were created successfully, False otherwise
        """
        if not self.create_directories(["docs/architecture"]):
            return False
        projection = architecture_readme_projection(title, directories, contract)
        return self.write_content(projection.target, projection.content)

    def create_scaffold_contract_docs(self, contract: ScaffoldContract) -> bool:
        """Create agent-facing docs and the machine-readable scaffold manifest."""
        if not self.create_directories(
            [
                ".kickstart",
                "docs/contracts",
                "docs/operations",
                "docs/decisions",
            ]
        ):
            return False

        docs: dict[str, str] = {
            projection.target: projection.content
            for projection in scaffold_docs_projections(contract, self._projection_profile())
        }
        docs[".kickstart/scaffold.json"] = contract.manifest_json(self.name)
        return all(self.write_content(target, content) for target, content in docs.items())

    def _projection_profile(self) -> str:
        """Return the docs projection profile used for managed docs renders."""
        return PROFILE_DEFAULT

    def write_templates_from_plan(self, template_plan: TemplatePlan) -> bool:
        """Write multiple template files from a typed plan.

        Args:
            template_plan: Typed template render plan

        Returns:
            True if all templates were written successfully, False otherwise
        """
        def write_single_template(entry: TemplatePlanEntry) -> bool:
            """Write a single template entry."""
            return self.write_template(entry.target, entry.template, **entry.vars)

        # Use batch operation wrapper for standardized error collection
        collector = batch_operation_wrapper(
            items=template_plan.entries(),
            operation_func=write_single_template,
            operation_name="Template writing",
            item_name_func=lambda entry: f"{entry.target} (from {entry.template})"
        )

        return not collector.has_errors()

    def create_with_github(self, success_message: str, create_repo_fn: Callable[[], bool | None] | None = None) -> None:
        """Create project and optionally create GitHub repository.
        
        Args:
            success_message: Message to log on successful creation
            create_repo_fn: Function to call for GitHub repo creation
        """
        self.log_success(success_message)
        if create_repo_fn:
            create_repo_fn()

    def execute_create_flow(self, 
                          directories: Sequence[str],
                          template_plan: TemplatePlan,
                          architecture_title: str,
                          scaffold_contract: ScaffoldContract,
                          success_message: str,
                          language_setup_fn: Callable[[], bool] | None = None,
                          additional_setup_fn: Callable[[], bool] | None = None,
                          github_create_fn: Callable[[], bool | None] | None = None) -> bool:
        """Execute the common create flow for generators.
        
        Args:
            directories: Directories to create
            template_plan: Typed template render plan
            architecture_title: Title for architecture documentation
            scaffold_contract: Agent and machine-readable scaffold metadata
            success_message: Success message to log
            language_setup_fn: Optional function for language-specific setup
            additional_setup_fn: Optional function for additional setup
            github_create_fn: Optional function for GitHub repo creation
            
        Returns:
            True if project was created successfully, False otherwise
        """
        if not self.create_project():
            raise ProjectCreationError(
                f"Project '{self.name}' was not created: directory '{self.project}' "
                "already exists or is not accessible."
            )

        # Use error collector for standardized error tracking
        error_collector = ErrorCollector("Project creation")

        # Create project structure
        if not self.init_basic_structure(directories):
            error_collector.add_error("Failed to create directory structure")
        else:
            error_collector.increment_success()
        error_collector.increment_total()

        # Write template files
        if not self.write_templates_from_plan(template_plan):
            error_collector.add_error("Failed to write template files")
        else:
            error_collector.increment_success()
        error_collector.increment_total()

        # Create architecture docs
        with safe_operation_context("Architecture documentation creation", log_errors=True):
            if not self.create_architecture_docs(architecture_title, directories, scaffold_contract):
                error_collector.add_error("Failed to create architecture documentation")
            else:
                error_collector.increment_success()
        error_collector.increment_total()

        # Create the generated scaffold contract
        with safe_operation_context("Scaffold contract documentation creation", log_errors=True):
            if not self.create_scaffold_contract_docs(scaffold_contract):
                error_collector.add_error("Failed to create scaffold contract documentation")
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

        # Fail before announcing success or creating a GitHub repo: a partial
        # scaffold must never produce a success banner or remote side effects.
        if error_collector.has_errors():
            error_collector.log_summary()
            error_collector.report_failures()
            raise ProjectCreationError(
                f"Project '{self.name}' was generated with errors: {'; '.join(error_collector.errors)}"
            )

        # Success message and GitHub integration
        with safe_operation_context("GitHub integration", log_errors=True):
            self.create_with_github(success_message, github_create_fn)
            error_collector.increment_success()
        error_collector.increment_total()

        error_collector.log_summary()
        return True
