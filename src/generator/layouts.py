"""Directory layout plans for project generators."""

from collections.abc import Sequence

from src.generator.scaffold_contract import ScaffoldContract
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


def cli_directories(language: str | None = None) -> list[str]:
    """Return the base directory layout for modular CLI projects."""
    command_directories = {
        "python": ["src/cli", "src/cli/commands"],
        "rust": ["src/cli"],
        "typescript": ["bin", "src/commands"],
    }.get(language or "", ["src/cli"])
    return [
        *command_directories,
        "src/config",
        "src/clients",
        "src/model",
        "src/operations",
        "src/output",
        "src/error",
        "tests",
        *scaffold_contract_directories(),
    ]


# Purpose of each generated directory, keyed by the longest matching prefix.
# This feeds the generated docs/architecture/README.md so humans can orient
# in an agent-written repo without reverse-engineering the layout.
DIRECTORY_PURPOSES: dict[str, str] = {
    "src/routes": "HTTP surface: one module per route group",
    "src/api": "service-level operations behind the routes",
    "src/model": "entities, DTOs, and persistence-facing types",
    "src/clients": "clients for external services (database, cache, ...)",
    "src/handler": "cross-cutting request handling (auth, middleware)",
    "src/config": "environment parsing and settings",
    "src/cli": "command adapters for the CLI framework",
    "src/operations": "CLI use-case implementations",
    "src/output": "output formatting and rendering",
    "src/error": "error types and exit-code mapping",
    "src/commands": "framework-native CLI command files",
    "src": "application source",
    "tests/unit": "fast, isolated tests",
    "tests/integration": "tests that touch external services",
    "tests/fixtures": "shared test data",
    "tests": "project tests",
    "migrations": "database schema migrations",
    "docs/architecture": "structure and boundary notes (this file)",
    "docs/contracts": "public and external surfaces",
    "docs/operations": "local development, validation, and deploy notes",
    "docs/decisions": "durable design decisions",
    "docs": "project documentation",
    ".kickstart": "machine-readable scaffold metadata",
    ".github/workflows": "CI workflows",
    "apps": "deployable applications",
    "services": "deployable services",
    "libs": "shared code",
    "tools": "automation and internal CLIs",
    "infra/docker": "local container composition",
    "infra/terraform": "infrastructure as code",
    "infra/k8s": "Kubernetes manifests",
    "data": "seed data and schemas",
    "helm": "Helm chart for Kubernetes deployment",
}


def directory_purpose(directory: str) -> str | None:
    """Return the purpose for a directory using its longest known prefix."""
    candidates = [prefix for prefix in DIRECTORY_PURPOSES if directory == prefix or directory.startswith(f"{prefix}/")]
    if not candidates:
        return None
    return DIRECTORY_PURPOSES[max(candidates, key=len)]


def render_architecture_readme(
    title: str,
    directories: Sequence[str],
    contract: ScaffoldContract | None,
) -> str:
    """Render the generated architecture README as a human-oriented module map."""
    lines = [
        f"# {title}",
        "",
        "Generated by kickstart. This map exists so humans can orient quickly in",
        "a repo where agents write most of the code; machine-readable metadata",
        "lives in `.kickstart/scaffold.json`.",
        "",
        "## Layout",
        "",
    ]

    described: dict[str, str] = {}
    for directory in (*directories, *scaffold_contract_directories()):
        purpose = directory_purpose(directory)
        if purpose is None:
            continue
        # Collapse nested entries onto their best-known prefix once.
        described.setdefault(directory, purpose)

    for directory in sorted(described):
        lines.append(f"- `{directory}/` — {described[directory]}")

    if contract is not None:
        extensions = contract.service_extensions.manifest()
        if extensions:
            lines.extend(["", "## Selected Capabilities", ""])
            for kind, value in sorted(extensions.items()):
                lines.append(f"- {kind}: `{value}` (see the matching client/handler module and its tests)")

        lines.extend(
            [
                "",
                "## Start Here",
                "",
                f"- Entrypoint: `{contract.entrypoint}`" if contract.entrypoint else "- Entrypoint: see `src/`",
                "- `make check` runs the project's full verification (lint, types, tests).",
                "- `docs/contracts/` documents the public surface; record decisions in `docs/decisions/`.",
            ]
        )

    return "\n".join(lines) + "\n"
