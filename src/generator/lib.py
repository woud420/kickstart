from collections.abc import Callable, Sequence
from pathlib import Path
from src.generator.base import BaseGenerator
from src.generator.layouts import cli_directories, library_directories
from src.generator.scaffold_contract import ScaffoldContract
from src.generator.specs import CliSpec, LibrarySpec
from src.generator.template_plan import TemplatePlan
from src.generator.template_plans import cli_template_plan, library_template_plan
from src.utils.github import create_repo
from src.utils.types import GeneratorConfig

class LibraryGenerator(BaseGenerator):
    lang: str
    gh: bool
    lang_template_dir: Path
    spec: LibrarySpec | CliSpec
    
    def __init__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, root: str | None = None) -> None:
        spec = LibrarySpec(name=name, language=lang, gh=gh, config=config, root=root)
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.lang = spec.language
        self.gh = spec.gh
        self.lang_template_dir = self.template_dir / self.lang

    def create(self) -> None:
        self._create_package_project(
            directories=library_directories(),
            template_plan=library_template_plan(self.lang),
            architecture_title=f"{self.name} Library Docs",
            scaffold_contract=ScaffoldContract(project_kind="library", runtime="library"),
            success_message=f"{self.lang.title()} library '{self.name}' created successfully in '{self.project}'!",
            language_setup_fn=self._setup_language_specific_files,
        )

    def _create_package_project(
        self,
        directories: Sequence[str],
        template_plan: TemplatePlan,
        architecture_title: str,
        scaffold_contract: ScaffoldContract,
        success_message: str,
        language_setup_fn: Callable[[], bool],
    ) -> None:
        """Create a package-like project using the shared generator flow."""
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None

        self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            scaffold_contract=scaffold_contract,
            success_message=success_message,
            language_setup_fn=language_setup_fn,
            github_create_fn=github_create_fn if self.gh else None,
        )
    
    def _setup_language_specific_files(self) -> bool:
        """Setup language-specific files for library."""
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.toml.tpl")
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.toml.tpl")
        return True

class CLIGenerator(LibraryGenerator):
    def __init__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, root: str | None = None) -> None:
        spec = CliSpec(name=name, language=lang, gh=gh, config=config, root=root)
        super().__init__(spec.name, spec.language, spec.gh, spec.config, spec.root)
        self.spec = spec

    def create(self) -> None:
        self._create_package_project(
            directories=cli_directories(),
            template_plan=cli_template_plan(self.lang),
            architecture_title=f"{self.name} CLI Docs",
            scaffold_contract=ScaffoldContract(project_kind="cli", runtime="cli"),
            success_message=f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!",
            language_setup_fn=self._setup_cli_specific_files,
        )
    
    def _setup_cli_specific_files(self) -> bool:
        """Setup language-specific files for CLI."""
        if self.lang == "python":
            self.write_template("pyproject.toml", "python/pyproject.cli.toml.tpl")
            self.write_content("src/main.py", 'def main() -> None:\n    print("Hello from CLI")\n\n\nif __name__ == "__main__":\n    main()\n')
        elif self.lang == "rust":
            self.write_template("Cargo.toml", "rust/Cargo.cli.toml.tpl")
            self.write_content("src/main.rs", 'fn main() {\n    println!("Hello from CLI!");\n}\n')
        return True


LibGenerator = LibraryGenerator
