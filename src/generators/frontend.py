from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator

class FrontendGenerator(BaseGenerator):
    def __init__(self, name: str, config: dict, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.template_dir = self.template_dir / "react"

    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.create_directories([
            "src",
            "public",
            "tests",
            "architecture"
        ])

        # Write template files
        self.write_template(".gitignore", "gitignore.tpl")
        self.write_template("Dockerfile", "Dockerfile.tpl")
        self.write_template("Makefile", "Makefile.tpl")
        self.write_template("README.md", "README.md.tpl")
        self.write_template("package.json", "package.json.tpl")
        
        # Write direct content
        self.write_content("architecture/README.md", f"# {self.name} Frontend Docs\n")

        self.log_success(f"Frontend app '{self.name}' created successfully in '{self.project}'!")

def create_frontend(name: str, config: dict, root: str = None):
    """Factory function for backward compatibility"""
    generator = FrontendGenerator(name, config, root)
    generator.create()

