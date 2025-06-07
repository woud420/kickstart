from pathlib import Path
from typing import Dict, List, Optional
from src.utils.fs import write_file
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