"""Managed docs projections: pure renders of the scaffold contract.

Every artifact here belongs to the managed envelope (see
``docs/decisions/scaffold-metadata-architecture-review.md``): the docs
kickstart keeps aligned with the current standard. Each render is a pure
function of its explicit inputs — the scaffold contract, a projection
profile, and (for the architecture README) the generation-time title and
directory list — with no timestamps or environment reads, so the same
inputs always produce the same bytes.

Two of those inputs are generation-time knowledge the persisted manifest
does not record yet: the projection profile and the architecture
title/directories. Re-deriving expected docs from ``.kickstart/scaffold.json``
alone therefore covers the default-profile docs set today; closing that gap
is the render-inputs work in the metadata review's roadmap (§6 step 1).

``DocsProjection`` deliberately parallels ``ContentFile``
(``src/generator/file_plan.py``, the payload writes are converted into) and
``AgentWorkflowArtifact`` (``src/stack/agent_workflows.py``, whose payload
is a template reference instead of rendered content); it adds only the
stable ``id`` tooling needs to enumerate managed docs.

Each projection's file content is the rendered body wrapped in its ownership
fence (``src/generator/markers.py``): kickstart owns the fenced region and
nothing else, so user content added outside the fence survives every
re-render. The body render functions stay fence-free for direct reuse.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from src.generator.layouts import render_architecture_readme
from src.generator.markers import fence
from src.generator.scaffold_contract import ScaffoldContract
from src.utils.errors import MarkerError

ProjectionProfile = Literal["default", "typescript-cloudflare-worker"]

PROFILE_DEFAULT: ProjectionProfile = "default"
PROFILE_TYPESCRIPT_CLOUDFLARE_WORKER: ProjectionProfile = "typescript-cloudflare-worker"


@dataclass(frozen=True)
class DocsProjection:
    """One managed docs artifact.

    ``content`` is the full generated file (body wrapped in its ownership
    fence); ``body`` is the fence-free render, kept so compare/replace
    consumers never have to re-parse kickstart's own output.
    """

    id: str
    target: str
    content: str
    body: str


def scaffold_docs_projections(contract: ScaffoldContract, profile: ProjectionProfile = PROFILE_DEFAULT) -> tuple[DocsProjection, ...]:
    """Render the managed docs set emitted with every scaffold contract."""
    return (
        _fenced_projection("agent-map", "AGENTS.md", agent_map_content(profile)),
        _fenced_projection("contracts-readme", "docs/contracts/README.md", contracts_content(contract, profile)),
        _fenced_projection("operations-readme", "docs/operations/README.md", operations_content(contract, profile)),
        _fenced_projection("decisions-readme", "docs/decisions/README.md", decisions_content()),
    )


def architecture_readme_projection(
    title: str,
    directories: Sequence[str],
    contract: ScaffoldContract | None,
) -> DocsProjection:
    """Render the architecture README as a managed projection."""
    return _fenced_projection(
        "architecture-readme",
        "docs/architecture/README.md",
        render_architecture_readme(title, directories, contract),
    )


def _fenced_projection(artifact_id: str, target: str, body: str) -> DocsProjection:
    """Wrap a rendered body in its ownership fence as the file content.

    Generated files start as exactly one owned region; user content added
    outside the fence later is never read or rewritten by kickstart. Only
    markdown targets exist here — a non-markdown target must pick its marker
    style explicitly instead of inheriting HTML comments.
    """
    if not target.endswith(".md"):
        raise MarkerError(f"projection target '{target}' is not markdown; choose a marker style explicitly")
    return DocsProjection(id=artifact_id, target=target, content=fence(artifact_id, body), body=body)


def agent_map_content(profile: ProjectionProfile = PROFILE_DEFAULT) -> str:
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


def contracts_content(contract: ScaffoldContract, profile: ProjectionProfile = PROFILE_DEFAULT) -> str:
    """Render ``docs/contracts/README.md`` for the contract's project kind."""
    # Gate asymmetry is inherited from the pre-registry generator semantics:
    # the Agent Map keys off the profile alone, while contracts/operations
    # additionally require a worker-kind contract. ServiceGenerator only
    # selects the worker profile for worker-kind contracts today, so the
    # extra gate matters only if a future generator reuses the profile.
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


def operations_content(contract: ScaffoldContract, profile: ProjectionProfile = PROFILE_DEFAULT) -> str:
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
