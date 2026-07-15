"""Managed docs projections: pure renders of the scaffold contract.

Every artifact here belongs to the managed envelope (see
``docs/decisions/scaffold-metadata-architecture-review.md``): the docs
kickstart keeps aligned with the current standard. Each render is a pure
function of the scaffold contract and explicit generation inputs — no
timestamps, no environment reads — so tooling can re-derive the expected
content of a generated repo's managed docs and compare byte-for-byte.

Profile variants cover scaffolds whose docs form an explicit contract
(currently the TypeScript Cloudflare Worker profile). Generators select the
profile; the render functions stay pure.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from src.generator.layouts import render_architecture_readme
from src.generator.scaffold_contract import ScaffoldContract

PROFILE_DEFAULT = "default"
PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER = "typescript-cloudflare-worker"


@dataclass(frozen=True)
class DocsProjection:
    """One managed docs artifact: stable identifier, target path, content."""

    id: str
    target: str
    content: str


def scaffold_docs_projections(contract: ScaffoldContract, profile: str = PROFILE_DEFAULT) -> tuple[DocsProjection, ...]:
    """Render the managed docs set emitted with every scaffold contract."""
    return (
        DocsProjection(id="agent-map", target="AGENTS.md", content=agent_map_content(profile)),
        DocsProjection(
            id="contracts-readme",
            target="docs/contracts/README.md",
            content=contracts_content(contract, profile),
        ),
        DocsProjection(
            id="operations-readme",
            target="docs/operations/README.md",
            content=operations_content(contract, profile),
        ),
        DocsProjection(id="decisions-readme", target="docs/decisions/README.md", content=decisions_content()),
    )


def architecture_readme_projection(
    title: str,
    directories: Sequence[str],
    contract: ScaffoldContract | None,
) -> DocsProjection:
    """Render the architecture README as a managed projection."""
    return DocsProjection(
        id="architecture-readme",
        target="docs/architecture/README.md",
        content=render_architecture_readme(title, directories, contract),
    )


def agent_map_content(profile: str = PROFILE_DEFAULT) -> str:
    """Render ``AGENTS.md``, the repo's orientation map."""
    if profile == PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER:
        return _worker_agent_map_content()
    return (
        "# Agent Map\n\n"
        "- Start with `README.md` for project intent and first commands.\n"
        "- Use `docs/architecture/` for structure and boundaries.\n"
        "- Use `docs/contracts/` for public and external surfaces.\n"
        "- Use `docs/operations/` for local dev, validation, and deployment notes.\n"
        "- Use `docs/decisions/` for durable design decisions.\n"
        "- The docs above are the orientation surface. `.kickstart/scaffold.json` is "
        "kickstart's machine-readable scaffold state, consumed by tooling such as "
        "`kickstart adopt --check`.\n"
    )


def contracts_content(contract: ScaffoldContract, profile: str = PROFILE_DEFAULT) -> str:
    """Render ``docs/contracts/README.md`` for the contract's project kind."""
    if profile == PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER and contract.project_kind == "worker":
        return _worker_contracts_content()
    if contract.project_kind == "cli":
        cli_framework = contract.cli_framework or "language-native CLI framework"
        command_root = contract.command_root or "src/cli"
        operation_root = contract.operation_root or "src/operations"
        entrypoint = contract.entrypoint or "the generated process entrypoint"
        return (
            "# Contracts\n\n"
            f"- Command adapters use `{cli_framework}` and live under `{command_root}`.\n"
            f"- Product behavior belongs under `{operation_root}`.\n"
            f"- The process entrypoint is `{entrypoint}`.\n"
            "- Document commands, flags, environment variables, config files, output formats, "
            "exit codes, and package metadata here.\n"
        )
    return (
        "# Contracts\n\n"
        f"Document {contract.contract_subjects} here.\n"
    )


def operations_content(contract: ScaffoldContract, profile: str = PROFILE_DEFAULT) -> str:
    """Render ``docs/operations/README.md`` for the contract's project kind."""
    if profile == PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER and contract.project_kind == "worker":
        return _worker_operations_content()
    if contract.project_kind == "cli":
        return (
            "# Operations\n\n"
            "- `make install`: install package dependencies.\n"
            "- `make test`: run generated CLI smoke tests.\n"
            "- `make lint`: run the language linter (and clippy for Rust, ESLint for TypeScript).\n"
            "- `make fmt`: format sources in place.\n"
            "- `make typecheck`: run the language type checker.\n"
            "- `make check`: run lint + typecheck + tests; CI emits `.github/workflows/ci.yml` "
            "to invoke this same target.\n\n"
            "Add packaging, installation, release, signing, and operator runbooks here as the "
            "CLI matures.\n"
        )
    return (
        "# Operations\n\n"
        f"Document {contract.operations_subjects} here.\n"
        "\n"
        "Canonical make targets: `install`, `test`, `lint`, `fmt`, `typecheck`, `check`, "
        "`build`. Services with a `Dockerfile` also expose `docker-build`. The generated "
        "`.github/workflows/ci.yml` runs `make check` on push and pull requests.\n"
    )


def decisions_content() -> str:
    """Render ``docs/decisions/README.md``."""
    return (
        "# Decisions\n\n"
        "Record architecture and implementation decisions here. Keep entries short, dated, and "
        "linked to the generated scaffold contract when relevant.\n"
    )


def _worker_agent_map_content() -> str:
    return (
        "# Agent Map\n\n"
        "## Scope\n"
        "- This scaffold is an explicit TypeScript Cloudflare Worker contract.\n"
        "- The docs below are the orientation surface; `.kickstart/scaffold.json` "
        "records the contract as machine-readable scaffold state for tooling.\n\n"
        "## Code, tests, and config\n"
        "- Worker code: `src/index.ts`\n"
        "- Contract tests: `tests/worker.test.ts`\n"
        "- Runtime config: `wrangler.toml`\n"
        "- Tooling config: `package.json`, `tsconfig.json`, `Makefile`\n"
        "- Local env template: `.dev.vars.example` (copy to `.dev.vars` for local secrets)\n\n"
        "## Commands\n"
        "- Verify contract: `make check`\n"
        "- Local development: `make dev`\n"
        "- Deploy: `make deploy`\n\n"
        "## Deploy assumptions\n"
        "- Wrangler is authenticated (`wrangler login` locally or `CLOUDFLARE_API_TOKEN` in CI).\n"
        "- Cloudflare bindings and secrets are configured before `make deploy`.\n"
        "- Keep `SERVICE_NAME` bindings aligned between `wrangler.toml`, `.dev.vars`, and tests.\n\n"
        "## Do not hand-edit generated contract files\n"
        "- `.kickstart/scaffold.json`\n"
        "- `AGENTS.md`\n"
        "- `docs/contracts/README.md`\n"
        "- `docs/operations/README.md`\n\n"
        "Regenerate with kickstart when scaffold conventions change.\n"
    )


def _worker_contracts_content() -> str:
    return (
        "# Contracts\n\n"
        "## Scaffold identity\n"
        "- Kind: `worker`\n"
        "- Execution model: `cloudflare-worker`\n"
        "- Runtime platform: `cloudflare-workers`\n"
        "- Artifact: `wrangler`\n"
        "- Provider target: `cloudflare`\n\n"
        "See `.kickstart/scaffold.json` for the machine-readable source of truth.\n\n"
        "## TypeScript Worker handler contract\n"
        "- `src/index.ts` exports `default` and satisfies `ExportedHandler<Env>`.\n"
        "- `Env` bindings in TypeScript are mirrored in `wrangler.toml` and `.dev.vars`.\n"
        "- `/healthz` returns JSON health output and stays covered by tests.\n\n"
        "## Verification contract\n"
        "- Run `make check` before handoff.\n"
        "- `make check` runs `make typecheck` and `make test`.\n"
        "- `tests/worker.test.ts` validates the generated handler behavior.\n"
    )


def _worker_operations_content() -> str:
    return (
        "# Operations\n\n"
        "## Lifecycle flow\n"
        "1. Install dependencies: `make install`\n"
        "2. Verify scaffold contract: `make check`\n"
        "3. Run local worker runtime: `make dev`\n"
        "4. Deploy to Cloudflare Workers: `make deploy`\n\n"
        "## Verification files\n"
        "- `Makefile` contains lifecycle command wrappers.\n"
        "- `docs/contracts/README.md` describes runtime and handler constraints.\n"
        "- `.kickstart/scaffold.json` records command and platform metadata.\n\n"
        "## Deploy assumptions\n"
        "- Wrangler authentication is available.\n"
        "- Required bindings and secrets are configured before deploy.\n"
        "- Deployment target details live in `wrangler.toml`.\n"
    )
