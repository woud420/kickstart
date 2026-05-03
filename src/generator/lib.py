from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from src.generator.base import BaseGenerator
from src.generator.file_plan import ContentFile
from src.generator.layouts import cli_directories, library_directories
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from src.generator.specs import CliSpec, LibrarySpec
from src.generator.template_plan import TemplatePlan
from src.generator.template_plans import cli_template_plan, library_template_plan
from src.stack.profile import stack_registry
from src.stack.types import TemplateConfig
from src.utils.error_handling import LanguageNotSupportedError
from src.utils.github import create_repo
from src.utils.types import GeneratorConfig


PackageKind = Literal["library", "cli"]


@dataclass(frozen=True)
class PackageSetupPlan:
    """Language-specific templates and direct files for package-like projects."""

    templates: tuple[TemplateConfig, ...] = ()
    content_files: tuple[ContentFile, ...] = ()


PYTHON_LIBRARY_TEST_CONTENT = "def test_generated_scaffold() -> None:\n    assert True\n"
RUST_LIBRARY_CONTENT = "pub fn generated_scaffold_ready() -> bool {\n    true\n}\n"
PYTHON_CLI_MAIN_CONTENT = (
    'def main() -> None:\n    print("Hello from CLI")\n\n\nif __name__ == "__main__":\n    main()\n'
)
PYTHON_CLI_TEST_CONTENT = (
    "from src.main import main\n\n\n"
    "def test_generated_cli(capsys) -> None:\n"
    "    main()\n"
    '    assert "Hello from CLI" in capsys.readouterr().out\n'
)
RUST_CLI_MAIN_CONTENT = 'fn main() {\n    println!("Hello from CLI!");\n}\n'

LIBRARY_LANGUAGE_SETUP: dict[str, PackageSetupPlan] = {
    "python": PackageSetupPlan(
        templates=(TemplateConfig("pyproject.toml", "python/pyproject.toml.tpl"),),
        content_files=(
            ContentFile("src/__init__.py", ""),
            ContentFile("tests/test_smoke.py", PYTHON_LIBRARY_TEST_CONTENT),
        ),
    ),
    "rust": PackageSetupPlan(
        templates=(TemplateConfig("Cargo.toml", "rust/Cargo.lib.toml.tpl"),),
        content_files=(ContentFile("src/lib.rs", RUST_LIBRARY_CONTENT),),
    ),
}

CLI_LANGUAGE_SETUP: dict[str, PackageSetupPlan] = {
    "python": PackageSetupPlan(
        templates=(TemplateConfig("pyproject.toml", "python/pyproject.cli.toml.tpl"),),
        content_files=(
            ContentFile("src/__init__.py", ""),
            ContentFile("src/main.py", PYTHON_CLI_MAIN_CONTENT),
            ContentFile("tests/test_smoke.py", PYTHON_CLI_TEST_CONTENT),
        ),
    ),
    "rust": PackageSetupPlan(
        templates=(TemplateConfig("Cargo.toml", "rust/Cargo.cli.toml.tpl"),),
        content_files=(ContentFile("src/main.rs", RUST_CLI_MAIN_CONTENT),),
    ),
}


class LibraryGenerator(BaseGenerator):
    lang: str
    gh: bool
    lang_template_dir: Path
    spec: LibrarySpec | CliSpec
    
    def __init__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, root: str | None = None) -> None:
        spec = LibrarySpec(
            name=name,
            language=stack_registry.normalize_language(lang),
            gh=gh,
            config=config,
            root=root,
        )
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.lang = spec.language
        self.gh = spec.gh
        self.lang_template_dir = self.template_dir / self.lang

    def create(self) -> None:
        self._validate_package_language("library")
        self._create_package_project(
            directories=library_directories(),
            template_plan=library_template_plan(self.lang),
            architecture_title=f"{self.name} Library Docs",
            scaffold_contract=ScaffoldContract(
                project_kind="library",
                execution_models=("library",),
                runtime_platforms=("none",),
                artifacts=ScaffoldArtifacts(package=self.lang),
            ),
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
        self._write_package_setup(LIBRARY_LANGUAGE_SETUP.get(self.lang))
        return True

    def _write_package_setup(self, setup: PackageSetupPlan | None) -> None:
        """Write a package setup plan when the selected language has one."""
        if setup is None:
            return

        self.write_template_configs(setup.templates)
        self.write_content_files(setup.content_files)

    def _validate_package_language(self, package_kind: PackageKind) -> None:
        """Fail loudly when a package target does not have a complete setup plan."""
        profile = stack_registry.languages.get(self.lang)
        supported = _supported_package_languages(package_kind)
        is_supported = profile is not None and (profile.library if package_kind == "library" else profile.cli)
        if is_supported:
            return

        label = "CLI" if package_kind == "cli" else "library"
        raise LanguageNotSupportedError(
            "{label} language '{language}' is not supported. Supported {package_kind} languages: {supported}.".format(
                label=label,
                language=self.lang,
                package_kind=package_kind,
                supported=", ".join(supported),
            )
        )


class CLIGenerator(LibraryGenerator):
    def __init__(self, name: str, lang: str, gh: bool, config: GeneratorConfig, root: str | None = None) -> None:
        spec = CliSpec(name=name, language=stack_registry.normalize_language(lang), gh=gh, config=config, root=root)
        super().__init__(spec.name, spec.language, spec.gh, spec.config, spec.root)
        self.spec = spec

    def create(self) -> None:
        self._validate_package_language("cli")
        self._create_package_project(
            directories=cli_directories(),
            template_plan=cli_template_plan(self.lang),
            architecture_title=f"{self.name} CLI Docs",
            scaffold_contract=ScaffoldContract(
                project_kind="cli",
                execution_models=("cli",),
                runtime_platforms=("local",),
                artifacts=ScaffoldArtifacts(package=self.lang),
            ),
            success_message=f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!",
            language_setup_fn=self._setup_cli_specific_files,
        )
    
    def _setup_cli_specific_files(self) -> bool:
        """Setup language-specific files for CLI."""
        self._write_package_setup(CLI_LANGUAGE_SETUP.get(self.lang))
        return True


LibGenerator = LibraryGenerator


def _supported_package_languages(package_kind: PackageKind) -> tuple[str, ...]:
    """Return language ids with complete package setup for the package kind."""
    return tuple(
        sorted(
            language
            for language, profile in stack_registry.languages.items()
            if _supports_package_kind(profile.library, profile.cli, package_kind)
        )
    )


def _supports_package_kind(library: bool, cli: bool, package_kind: PackageKind) -> bool:
    """Return whether a language profile supports the package kind."""
    if package_kind == "library":
        return library
    return cli
