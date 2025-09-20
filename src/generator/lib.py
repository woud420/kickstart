from pathlib import Path
from typing import Any
from src.generator.base import BaseGenerator
from src.utils.github import create_repo

class LibraryGenerator(BaseGenerator):
    lang: str
    gh: bool
    lang_template_dir: Path
    
    def __init__(self, name: str, lang: str, gh: bool, config: dict[str, Any], root: str | None = None) -> None:
        super().__init__(name, config, root)
        self.lang = lang
        self.gh = gh
        self.lang_template_dir = self.template_dir / lang

    def create(self) -> None:
        directories: list[str] = ["src", "tests", "architecture"]
        
        template_configs: list[dict[str, str]] = [
            {"target": ".gitignore", "template": f"{self.lang}/gitignore.tpl"},
            {"target": "Makefile", "template": f"{self.lang}/Makefile.tpl"},
            {"target": "README.md", "template": f"{self.lang}/README.md.tpl"}
        ]
        
        architecture_title: str = f"{self.name} Library Docs"
        success_message: str = f"{self.lang.title()} library '{self.name}' created successfully in '{self.project}'!"

        def github_create_fn() -> Any:
            return create_repo(self.name) if self.gh else None
        
        self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            language_setup_fn=self._setup_language_specific_files,
            github_create_fn=github_create_fn if self.gh else None
        )
    
    def _setup_language_specific_files(self) -> None:
        """Setup language-specific files for library."""
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

class CLIGenerator(LibraryGenerator):
    def create(self) -> None:
        directories: list[str] = ["src", "tests", "architecture"]
        
        template_configs: list[dict[str, str]] = [
            {"target": ".gitignore", "template": f"{self.lang}/gitignore.tpl"},
            {"target": "Makefile", "template": f"{self.lang}/Makefile.tpl"},
            {"target": "README.md", "template": f"{self.lang}/README.md.tpl"}
        ]
        
        architecture_title: str = f"{self.name} CLI Docs"
        success_message: str = f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!"

        def github_create_fn() -> Any:
            return create_repo(self.name) if self.gh else None
        
        self.execute_create_flow(
            directories=directories,
            template_configs=template_configs,
            architecture_title=architecture_title,
            success_message=success_message,
            language_setup_fn=self._setup_cli_specific_files,
            github_create_fn=github_create_fn if self.gh else None
        )
    
    def _setup_cli_specific_files(self) -> None:
        """Setup language-specific files for CLI."""
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.cli.toml.tpl")
            self.write_content("src/main.py", 'import sys\nprint("Hello from CLI")\nsys.exit(0)\n')
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.cli.toml.tpl")
            self.write_content("src/main.rs", 'fn main() {\n    println!("Hello from CLI!");\n}\n')

