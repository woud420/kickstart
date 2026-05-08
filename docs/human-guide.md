# Human Guide

kickstart creates project scaffolds so the first hour of setup is repeatable instead of hand-built.

## Project Types

| Type | Command | Use For |
| --- | --- | --- |
| Service | `kickstart create service NAME --lang python` | Backend APIs and microservices |
| Frontend | `kickstart create frontend NAME` | React/Vite/Bun apps |
| Library | `kickstart create lib NAME --lang python` | Reusable packages |
| CLI | `kickstart create cli NAME --lang rust` | Command-line tools |
| System | `kickstart create system NAME` | Composition repo containing apps, services, libs, tools, infrastructure, docs, and agent metadata |

## Service Options

Languages:

- `python`: FastAPI by default, or `--framework minimal`
- `typescript` or `ts`: Bun + Fastify
- `rust`: Actix-web
- `cpp`: C++20 + CMake
- `go`: minimal `net/http`

Execution model:

- `container`: default service runtime
- `cloudflare-workers`: TypeScript or Rust Worker scaffold. Singular forms such as `cloudflare-worker` are accepted aliases, but docs should use the plural canonical name.

Implemented service extensions:

- `--database postgres`
- `--cache redis`
- `--auth jwt`

Support is intentionally narrow:

- Python/FastAPI container services support Postgres, Redis, and JWT.
- Rust container services support Redis and JWT.
- TypeScript container services support Postgres.

Other language/runtime/framework combinations fail loudly until their templates are implemented.

## Library And CLI Options

Python and Rust are the supported library targets. Python, Rust, and TypeScript are the supported CLI targets.

CLI scaffolds use the same agent-facing architecture across languages, with framework-native command adapters:

- Rust: clap derive in `src/cli/`.
- Python: Typer app in `src/cli/app.py` with commands in `src/cli/commands/`.
- TypeScript: oclif bin scripts in `bin/`, shared command base in `src/base-command.ts`, and commands in `src/commands/`.
- `src/config/`: configuration loading.
- `src/clients/`: external API/client boundaries.
- `src/model/`: DTOs and typed data boundaries.
- `src/operations/`: command use cases.
- `src/output/`: human and machine output formatting.
- `src/error/`: errors and exit codes.

Rust CLIs keep only `src/main.rs` at the source root. Python includes `src/__init__.py` and `src/main.py`. TypeScript follows oclif and keeps `src/base-command.ts` as the only direct source-root adapter. Other languages fail loudly until they have complete package setup, source files, and validation commands.

## System Options

Provider target:

- `multi`: AWS, GCP, and Cloudflare entrypoints
- `aws`, `gcp`, `cloudflare`: provider-specific entrypoints
- `none`: no cloud provider assumptions

Platform profile:

- `kubernetes`: Kustomize by default, Helm with `--helm`
- `cloudflare-workers`: Wrangler-oriented Worker runtime notes
- `hybrid`: Kubernetes plus Cloudflare Workers

Workspace tooling:

- `none`: default; no root language/package manager assumption
- `bun-turbo`: emits root `package.json`, `turbo.json`, `bunfig.toml`, shared TypeScript config, and `packages/`

Artifact model:

- Dockerfiles build container images.
- Kubernetes is the platform for container workloads.
- Kustomize and Helm are Kubernetes artifact styles.
- Wrangler is the Cloudflare Worker artifact path.
- Cloudflare Containers are not implemented yet. Treat them as a future Cloudflare runtime, not as the current Cloudflare Worker scaffold.

Knowledge adapter:

- `none`: default; no Backstage or Obsidian metadata
- `obsidian`: adds Obsidian vault settings
- `backstage`: adds Backstage catalog/template files
- `both`: adds both knowledge-system integrations

Generated project docs are not optional. Every project gets `AGENTS.md`, `docs/architecture/`, `docs/contracts/`, `docs/operations/`, `docs/decisions/`, and `.kickstart/scaffold.json`.

## Building On Top

Prefer extending the typed plan layers before adding generator branches:

- Directory plans live in `src/generator/layouts.py`.
- Template plans live in `src/generator/template_plans.py`.
- Service language setup plans live in `src/generator/language_setup.py`.
- The generated scaffold contract lives in `src/generator/scaffold_contract.py`.
- Stack choices live in `src/stack/`.
- System generation currently lives in `src/generator/monorepo.py` and `src/templates/monorepo/` for historical compatibility.

When adding a new scaffold option, add generated-output tests for the affected project type before refactoring that path.

## Project Tooling

kickstart supports Python `>=3.12,<3.15`. Use `make check` before committing. Use `make package` for wheel/source builds and `make binary` for a local standalone binary.
