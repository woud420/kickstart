"""Directory layout plans for project generators."""

from src.stack.profile import SystemSelection, stack_registry


def scaffold_contract_directories() -> list[str]:
    """Return docs and metadata directories generated for every project."""
    return [
        ".kickstart",
        "docs/architecture",
        "docs/contracts",
        "docs/operations",
        "docs/decisions",
    ]


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
        *scaffold_contract_directories(),
    ]


def worker_directories() -> list[str]:
    """Return the base directory layout for Cloudflare Worker services."""
    return ["src", "tests", *scaffold_contract_directories()]


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


def system_directories(selection: SystemSelection) -> list[str]:
    """Return the base directory layout for a system stack selection."""
    directories = [
        "apps",
        "infra/docker",
        "infra/terraform/modules/example_module",
        "infra/terraform/modules/service_runtime",
        *(f"infra/terraform/env/{env}" for env in stack_registry.environments),
        ".github/workflows",
        "libs",
        "services",
        "tools",
        "data/postgres",
        "knowledge",
        *scaffold_contract_directories(),
        "docs/agents",
        "docs/data",
        "docs/knowledge",
        "docs/runbooks",
        "reports",
        "scripts",
    ]
    if selection.uses_bun_turbo:
        directories[1:1] = [
            "packages",
            "config/eslint",
            "config/tsconfig",
        ]
        workflows_index = directories.index(".github/workflows") + 1
        directories[workflows_index:workflows_index] = ["frontend"]
    if selection.uses_cloudflare_workers:
        return directories + ["infra/cloudflare/workers"]
    return directories


monorepo_directories = system_directories


def frontend_directories() -> list[str]:
    """Return the base directory layout for frontend projects."""
    return ["src", "public", "tests", *scaffold_contract_directories()]


def library_directories() -> list[str]:
    """Return the base directory layout for library projects."""
    return ["src", "tests", *scaffold_contract_directories()]


def cli_directories() -> list[str]:
    """Return the base directory layout for CLI projects."""
    return ["src", "tests", *scaffold_contract_directories()]
