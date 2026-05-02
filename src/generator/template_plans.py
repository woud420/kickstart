"""Reusable template render plans for generators."""

from src.generator.template_plan import TemplatePlan
from src.stack.types import TemplateConfig


def frontend_template_plan() -> TemplatePlan:
    """Return the template plan for frontend projects."""
    return TemplatePlan.from_templates(
        [
            TemplateConfig("index.html", "index.html.tpl"),
            TemplateConfig(".gitignore", "gitignore.tpl"),
            TemplateConfig("Dockerfile", "Dockerfile.tpl"),
            TemplateConfig("Makefile", "Makefile.tpl"),
            TemplateConfig("README.md", "README.md.tpl"),
            TemplateConfig("package.json", "package.json.tpl"),
            TemplateConfig("tsconfig.json", "tsconfig.json.tpl"),
            TemplateConfig("vite.config.ts", "vite.config.ts.tpl"),
            TemplateConfig("src/App.tsx", "src/App.tsx.tpl"),
            TemplateConfig("src/main.tsx", "src/main.tsx.tpl"),
            TemplateConfig("tests/App.test.tsx", "tests/App.test.tsx.tpl"),
        ]
    )


def library_template_plan(language: str) -> TemplatePlan:
    """Return the template plan for library projects."""
    return _package_template_plan(language)


def cli_template_plan(language: str) -> TemplatePlan:
    """Return the template plan for CLI projects."""
    return _package_template_plan(language)


def _package_template_plan(language: str) -> TemplatePlan:
    """Return shared package templates for library-like projects."""
    return TemplatePlan.from_templates(
        [
            TemplateConfig(".gitignore", f"{language}/gitignore.tpl"),
            TemplateConfig("Makefile", f"{language}/Makefile.tpl"),
            TemplateConfig("README.md", f"{language}/README.md.tpl"),
        ]
    )
