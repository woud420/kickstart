"""Directory layout plans for project generators."""

from src.stack.profile import MonorepoSelection, stack_registry


def service_directories() -> list[str]:
    """Return the base directory layout for container service projects."""
    return [
        "src/model",
        "src/api",
        "src/routes",
        "src/handler",
        "src/clients",
        "src/config",
        "tests/unit/model",
        "tests/unit/api",
        "tests/unit/routes",
        "tests/integration/api",
        "tests/integration/clients",
        "tests/fixtures",
        "docs",
    ]


def worker_directories() -> list[str]:
    """Return the base directory layout for Cloudflare Worker services."""
    return ["src", "tests", "docs"]


def python_package_directories() -> list[str]:
    """Return Python package directories that need ``__init__.py`` files."""
    return [
        "src",
        "src/model",
        "src/api",
        "src/routes",
        "src/handler",
        "src/clients",
        "src/config",
        "tests",
        "tests/unit",
        "tests/unit/model",
        "tests/unit/api",
        "tests/unit/routes",
        "tests/integration",
        "tests/integration/api",
        "tests/integration/clients",
        "tests/fixtures",
    ]


def monorepo_directories(selection: MonorepoSelection) -> list[str]:
    """Return the base directory layout for a monorepo stack selection."""
    directories = [
        "apps",
        "packages",
        "config/eslint",
        "config/tsconfig",
        "infra/docker",
        "infra/terraform/modules/example_module",
        "infra/terraform/modules/service_runtime",
        *(f"infra/terraform/env/{env}" for env in stack_registry.environments),
        ".github/workflows",
        "architecture",
        "frontend",
        "libs",
        "services",
        "data/postgres",
        "knowledge",
        "docs/adr",
        "docs/agents",
        "docs/architecture",
        "docs/data",
        "docs/knowledge",
        "docs/runbooks",
        "reports",
        "scripts",
    ]
    if selection.uses_cloudflare_workers:
        return directories + ["infra/cloudflare/workers"]
    return directories


def frontend_directories() -> list[str]:
    """Return the base directory layout for frontend projects."""
    return ["src", "public", "tests", "architecture"]


def library_directories() -> list[str]:
    """Return the base directory layout for library projects."""
    return ["src", "tests", "docs", "architecture"]


def cli_directories() -> list[str]:
    """Return the base directory layout for CLI projects."""
    return ["src", "tests", "docs", "architecture"]
