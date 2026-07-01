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
from src.utils.errors import LanguageNotSupportedError
from src.utils.github import create_repo
from src.utils.types import GeneratorConfig


PackageKind = Literal["library", "cli"]


@dataclass(frozen=True)
class PackageSetupPlan:
    """Language-specific templates and direct files for package-like projects."""

    templates: tuple[TemplateConfig, ...] = ()
    content_files: tuple[ContentFile, ...] = ()


PYTHON_LIBRARY_TEST_CONTENT = '''"""Smoke tests: the generated library package must import."""

import src


def test_package_imports() -> None:
    assert src is not None
'''
RUST_LIBRARY_CONTENT = "pub fn generated_scaffold_ready() -> bool {\n    true\n}\n"
LIBRARY_LANGUAGE_SETUP: dict[str, PackageSetupPlan] = {
    "python": PackageSetupPlan(
        templates=(TemplateConfig("pyproject.toml", "python/pyproject.toml.tpl"),),
        content_files=(
            ContentFile("src/__init__.py", ""),
            ContentFile("tests/test_smoke.py", PYTHON_LIBRARY_TEST_CONTENT),
        ),
    ),
    "rust": PackageSetupPlan(
        templates=(
            TemplateConfig("Cargo.toml", "rust/Cargo.lib.toml.tpl"),
            TemplateConfig("rust-toolchain.toml", "rust/rust-toolchain.toml.tpl"),
        ),
        content_files=(ContentFile("src/lib.rs", RUST_LIBRARY_CONTENT),),
    ),
}

CLI_LANGUAGE_SETUP: dict[str, PackageSetupPlan] = {
    "python": PackageSetupPlan(
        templates=(
            TemplateConfig("src/main.py", "cli/python/src/main.py.tpl"),
            TemplateConfig("src/cli/__init__.py", "cli/python/src/cli/__init__.py.tpl"),
            TemplateConfig("src/cli/app.py", "cli/python/src/cli/app.py.tpl"),
            TemplateConfig("src/cli/commands/__init__.py", "cli/python/src/cli/commands/__init__.py.tpl"),
            TemplateConfig("src/cli/commands/check.py", "cli/python/src/cli/commands/check.py.tpl"),
            TemplateConfig("src/config/__init__.py", "cli/python/src/config/__init__.py.tpl"),
            TemplateConfig("src/clients/__init__.py", "cli/python/src/clients/__init__.py.tpl"),
            TemplateConfig("src/model/__init__.py", "cli/python/src/model/__init__.py.tpl"),
            TemplateConfig("src/model/dto.py", "cli/python/src/model/dto.py.tpl"),
            TemplateConfig("src/operations/__init__.py", "cli/python/src/operations/__init__.py.tpl"),
            TemplateConfig("src/output/__init__.py", "cli/python/src/output/__init__.py.tpl"),
            TemplateConfig("src/error/__init__.py", "cli/python/src/error/__init__.py.tpl"),
            TemplateConfig("tests/test_cli_smoke.py", "cli/python/tests/test_cli_smoke.py.tpl"),
        ),
        content_files=(
            ContentFile("src/__init__.py", '__version__ = "0.1.0"\n'),
        ),
    ),
    "rust": PackageSetupPlan(
        templates=(
            TemplateConfig("src/main.rs", "cli/rust/src/main.rs.tpl"),
            TemplateConfig("src/cli/mod.rs", "cli/rust/src/cli/mod.rs.tpl"),
            TemplateConfig("src/cli/args.rs", "cli/rust/src/cli/args.rs.tpl"),
            TemplateConfig("src/cli/dispatch.rs", "cli/rust/src/cli/dispatch.rs.tpl"),
            TemplateConfig("src/config/mod.rs", "cli/rust/src/config/mod.rs.tpl"),
            TemplateConfig("src/clients/mod.rs", "cli/rust/src/clients/mod.rs.tpl"),
            TemplateConfig("src/model/mod.rs", "cli/rust/src/model/mod.rs.tpl"),
            TemplateConfig("src/model/dto.rs", "cli/rust/src/model/dto.rs.tpl"),
            TemplateConfig("src/operations/mod.rs", "cli/rust/src/operations/mod.rs.tpl"),
            TemplateConfig("src/output/mod.rs", "cli/rust/src/output/mod.rs.tpl"),
            TemplateConfig("src/error/mod.rs", "cli/rust/src/error/mod.rs.tpl"),
            TemplateConfig("tests/cli_smoke.rs", "cli/rust/tests/cli_smoke.rs.tpl"),
        ),
    ),
    "typescript": PackageSetupPlan(
        templates=(
            TemplateConfig("bin/dev.js", "cli/typescript/bin/dev.js.tpl"),
            TemplateConfig("bin/run.js", "cli/typescript/bin/run.js.tpl"),
            TemplateConfig("src/base-command.ts", "cli/typescript/src/base-command.ts.tpl"),
            TemplateConfig("src/commands/check.ts", "cli/typescript/src/commands/check.ts.tpl"),
            TemplateConfig("src/config/index.ts", "cli/typescript/src/config/index.ts.tpl"),
            TemplateConfig("src/clients/index.ts", "cli/typescript/src/clients/index.ts.tpl"),
            TemplateConfig("src/model/dto.ts", "cli/typescript/src/model/dto.ts.tpl"),
            TemplateConfig("src/operations/index.ts", "cli/typescript/src/operations/index.ts.tpl"),
            TemplateConfig("src/output/index.ts", "cli/typescript/src/output/index.ts.tpl"),
            TemplateConfig("src/error/index.ts", "cli/typescript/src/error/index.ts.tpl"),
            TemplateConfig("tests/cli-smoke.test.ts", "cli/typescript/tests/cli-smoke.test.ts.tpl"),
        ),
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
            directories=cli_directories(self.lang),
            template_plan=cli_template_plan(self.lang),
            architecture_title=f"{self.name} CLI Docs",
            scaffold_contract=ScaffoldContract(
                project_kind="cli",
                execution_models=("cli",),
                runtime_platforms=("local",),
                artifacts=ScaffoldArtifacts(package=self.lang),
                architecture="modular-cli",
                cli_framework=self._cli_framework(),
                command_root=self._command_root(),
                entrypoint=self._entrypoint(),
                operation_root="src/operations",
                src_root_files=self._src_root_files(),
            ),
            success_message=f"{self.lang.title()} CLI '{self.name}' created successfully in '{self.project}'!",
            language_setup_fn=self._setup_cli_specific_files,
        )
    
    def _setup_cli_specific_files(self) -> bool:
        """Setup language-specific files for CLI."""
        self._write_package_setup(CLI_LANGUAGE_SETUP.get(self.lang))
        return True

    def _src_root_files(self) -> tuple[str, ...]:
        """Return expected language root files below ``src/`` for CLI contracts."""
        return {
            "python": ("__init__.py", "main.py"),
            "rust": ("main.rs",),
            "typescript": ("base-command.ts",),
        }.get(self.lang, ())

    def _cli_framework(self) -> str:
        """Return the default CLI framework for the selected language."""
        return {
            "python": "typer",
            "rust": "clap",
            "typescript": "oclif",
        }.get(self.lang, "custom")

    def _command_root(self) -> str:
        """Return the framework-native command adapter root."""
        return {
            "python": "src/cli/commands",
            "rust": "src/cli",
            "typescript": "src/commands",
        }.get(self.lang, "src/cli")

    def _entrypoint(self) -> str:
        """Return the generated process entrypoint."""
        return {
            "python": "src/main.py",
            "rust": "src/main.rs",
            "typescript": "bin/run.js",
        }.get(self.lang, "src/main")


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
