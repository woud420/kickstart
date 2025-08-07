from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator
from src.generators.mixins import GitHubMixin, CommonTemplatesMixin
from src.utils.github import create_repo

class LibraryGenerator(BaseGenerator, GitHubMixin, CommonTemplatesMixin):
    def __init__(self, name: str, lang: str, gh: bool, config: dict, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.lang_template_dir = self.template_dir / lang

    def _create_structure(
        self,
        docs_label: str,
        python_template: str,
        rust_template: str,
    ) -> None:
        # Create project structure
        self.init_basic_structure([
            "src",
            "tests",
            "architecture"
        ])

        # Write common template files
        self.write_common_lib_templates(self.lang)

        # Write direct content
        self.create_architecture_docs(f"{self.name} {docs_label}")

        # Language-specific files
        if self.lang == "python":
            self.write_template("pyproject.toml", python_template)
        elif self.lang == "rust":
            self.write_template("Cargo.toml", rust_template)

    def create(self) -> None:
        if not self.create_project():
            return

        self._create_structure(
            "Library Docs",
            "python/pyproject.toml.tpl",
            "rust/Cargo.toml.tpl",
        )

        self.log_success(
            f"{self.lang.title()} library '{self.name}' created successfully in '{self.project}'!"
        )

        self.create_github_repo_if_requested()

class CLIGenerator(LibraryGenerator):
    def create(self) -> None:
        if not self.create_project():
            return

        self._create_structure(
            "CLI Docs",
            "python/pyproject.cli.toml.tpl",
            "rust/Cargo.cli.toml.tpl",
        )

        if self.lang == "python":
            self.write_content(
                "src/main.py",
                'import sys\nprint("Hello from CLI")\nsys.exit(0)\n',
            )
        elif self.lang == "rust":
            self.write_content(
                "src/main.rs",
                'fn main() {\n    println!("Hello from CLI!");\n}\n',
            )

        self.log_success(
            f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!"
        )

        self.create_github_repo_if_requested()
