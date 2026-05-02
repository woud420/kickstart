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


def python_service_core_template_plan(framework: str | None) -> TemplatePlan:
    """Return the core Python service template plan for the selected framework."""
    if framework == "minimal":
        return TemplatePlan.from_templates(
            [
                TemplateConfig("src/main.py", "python/extensions/minimal/core/main.py.tpl"),
                TemplateConfig("requirements.txt", "python/extensions/minimal/core/requirements.txt.tpl"),
            ]
        )

    return TemplatePlan.from_templates(
        [
            TemplateConfig("src/main.py", "python/core/main.py.tpl"),
            TemplateConfig("src/model/__init__.py", "python/core/model/__init__.py.tpl"),
            TemplateConfig("src/model/entities.py", "python/core/model/entities.py.tpl"),
            TemplateConfig("src/model/dto.py", "python/core/model/dto.py.tpl"),
            TemplateConfig("src/model/repository.py", "python/core/model/repository.py.tpl"),
            TemplateConfig("src/api/__init__.py", "python/core/api/__init__.py.tpl"),
            TemplateConfig("src/api/services.py", "python/core/api/services.py.tpl"),
            TemplateConfig("src/routes/__init__.py", "python/core/routes/__init__.py.tpl"),
            TemplateConfig("src/routes/users.py", "python/core/routes/users.py.tpl"),
            TemplateConfig("src/routes/health.py", "python/core/routes/health.py.tpl"),
            TemplateConfig("src/config/__init__.py", "python/core/config/__init__.py.tpl"),
            TemplateConfig("src/config/settings.py", "python/core/config/settings.py.tpl"),
            TemplateConfig("requirements.txt", "python/core/requirements.txt.tpl"),
        ]
    )


def _package_template_plan(language: str) -> TemplatePlan:
    """Return shared package templates for library-like projects."""
    return TemplatePlan.from_templates(
        [
            TemplateConfig(".gitignore", f"{language}/gitignore.tpl"),
            TemplateConfig("Makefile", f"{language}/Makefile.tpl"),
            TemplateConfig("README.md", f"{language}/README.md.tpl"),
        ]
    )
