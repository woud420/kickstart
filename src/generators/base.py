from pathlib import Path
from typing import Dict, List, Optional
from src.utils.fs import write_file, compose_template
from src.utils.logger import success, warn

class BaseGenerator:
    def __init__(self, name: str, config: dict, root: Optional[str] = None):
        self.name = name
        self.config = config
        self.project = Path(root) / name if root else Path(name)
        self.template_dir = Path(__file__).parent.parent / "templates"

    def create_project(self) -> bool:
        """Check if the project directory exists.

        Return ``True`` when it doesn't exist; otherwise log a warning and
        return ``False``.
        """
        if self.project.exists():
            warn(f"Directory '{self.project}' already exists.")
            return False
        return True

    def create_directories(self, directories: List[str]) -> None:
        """Create multiple directories under the project root."""
        for directory in directories:
            (self.project / directory).mkdir(parents=True, exist_ok=True)

    def write_template(self, target: str, template_path: str, **vars) -> None:
        """Write a template file to the project."""
        if isinstance(template_path, str) and not Path(template_path).is_absolute():
            template_path = self.template_dir / template_path
        write_file(self.project / target, template_path, service_name=self.name, **vars)

    def write_content(self, target: str, content: str) -> None:
        """Write direct content to a file in the project."""
        write_file(self.project / target, content)

    def log_success(self, message: str) -> None:
        """Log a success message."""
        success(message)

    def get_common_vars(self) -> Dict[str, str]:
        """Get common template variables."""
        return {"service_name": self.name}

    def init_basic_structure(self, dirs: List[str]) -> None:
        """Create the base directory structure for a new project."""
        self.create_directories(dirs)

    def create_architecture_docs(self, title: str) -> None:
        """Create the architecture documentation directory and README."""
        self.create_directories(["architecture"])
        self.write_content("architecture/README.md", f"# {title}\n")

    def write_standardized_template(self, target: str, template_type: str, lang: str, **extra_vars) -> None:
        """Write a standardized template using shared patterns."""
        from src.utils.template_config import TemplateConfig
        
        # Get language-specific variables
        template_vars = TemplateConfig.get_vars(lang, self.name)
        template_vars.update(extra_vars)
        
        # Generate content based on template type
        if template_type == "env":
            content = TemplateConfig.get_shared_env_template()
        else:
            # Fall back to regular template
            template_path = self.template_dir / lang / f"{template_type}.tpl"
            if template_path.exists():
                content = template_path.read_text()
            else:
                self.log_success(f"Template not found: {template_path}")
                return
        
        # Replace variables
        for key, value in template_vars.items():
            content = content.replace(f"{{{{{key.upper()}}}}}", str(value))
        
        # Write to file
        write_file(self.project / target, content)
