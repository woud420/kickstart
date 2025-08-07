from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.generators.mixins import GitHubMixin

class FrontendGenerator(BaseGenerator, GitHubMixin):
    def __init__(self, name: str, gh: bool, config: dict, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.template_dir = self.template_dir / "react"
        self.gh = gh

    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.init_basic_structure([
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
        self.create_architecture_docs(f"{self.name} Frontend Docs")

        self.log_success(f"Frontend app '{self.name}' created successfully in '{self.project}'!")

        self.create_github_repo_if_requested()
