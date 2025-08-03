from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.generators.mixins import GitHubMixin, CommonTemplatesMixin

class LibraryGenerator(BaseGenerator, GitHubMixin, CommonTemplatesMixin):
    def __init__(self, name: str, lang: str, gh: bool, config: dict, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.lang_template_dir = self.template_dir / lang

    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.init_basic_structure([
            "src",
            "tests",
            "architecture"
        ])

        # Write common template files
        self.write_common_lib_templates(self.lang)
        
        # Write direct content
        self.create_architecture_docs(f"{self.name} Library Docs")

        # Language-specific files
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

        self.log_success(f"{self.lang.title()} library '{self.name}' created successfully in '{self.project}'!")

        self.create_github_repo_if_requested()

class CLIGenerator(LibraryGenerator):
    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.init_basic_structure([
            "src",
            "tests",
            "architecture"
        ])

        # Write common template files
        self.write_common_lib_templates(self.lang)
        
        # Write direct content
        self.create_architecture_docs(f"{self.name} CLI Docs")

        # Language-specific files
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.cli.toml.tpl")
            self.write_content("src/main.py", 'import sys\nprint("Hello from CLI")\nsys.exit(0)\n')
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.cli.toml.tpl")
            self.write_content("src/main.rs", 'fn main() {\n    println!("Hello from CLI!");\n}\n')

        self.log_success(f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!")

        self.create_github_repo_if_requested()

