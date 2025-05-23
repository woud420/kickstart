from pathlib import Path
from typing import Optional
from src.generators.base import BaseGenerator

class LibraryGenerator(BaseGenerator):
    def __init__(self, name: str, lang: str, config: dict, root: Optional[str] = None):
        super().__init__(name, config, root)
        self.lang = lang
        self.lang_template_dir = self.template_dir / lang

    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.create_directories([
            "src",
            "tests",
            "architecture"
        ])

        # Write common template files
        self.write_template(".gitignore", f"{self.lang}/gitignore.tpl")
        self.write_template("Makefile", f"{self.lang}/Makefile.tpl")
        self.write_template("README.md", f"{self.lang}/README.md.tpl")
        
        # Write direct content
        self.write_content("architecture/README.md", f"# {self.name} Library Docs\n")

        # Language-specific files
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")

        self.log_success(f"{self.lang.title()} library '{self.name}' created successfully in '{self.project}'!")

class CLIGenerator(LibraryGenerator):
    def create(self) -> None:
        if not self.create_project():
            return

        # Create project structure
        self.create_directories([
            "src",
            "tests",
            "architecture"
        ])

        # Write common template files
        self.write_template(".gitignore", f"{self.lang}/gitignore.tpl")
        self.write_template("Makefile", f"{self.lang}/Makefile.tpl")
        self.write_template("README.md", f"{self.lang}/README.md.tpl")
        
        # Write direct content
        self.write_content("architecture/README.md", f"# {self.name} CLI Docs\n")

        # Language-specific files
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.cli.toml.tpl")
            self.write_content("src/main.py", 'import sys\nprint("Hello from CLI")\nsys.exit(0)\n')
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.cli.toml.tpl")
            self.write_content("src/main.rs", 'fn main() {\n    println!("Hello from CLI!");\n}\n')

        self.log_success(f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!")

def create_lib(name: str, lang: str, config: dict, root: str = None):
    """Factory function for backward compatibility"""
    generator = LibraryGenerator(name, lang, config, root)
    generator.create()

def create_cli(name: str, lang: str, config: dict, root: str = None):
    """Factory function for backward compatibility"""
    generator = CLIGenerator(name, lang, config, root)
    generator.create()

