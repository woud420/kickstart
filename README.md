# kickstart

kickstart is a scaffolding tool for generating project structure, services, workers, frontends, libraries, CLIs, and systems.

The goal is to eliminate the repeated setup work that humans and agents otherwise redo at the start of every project: directories, templates, Docker/Kubernetes/Cloudflare files, typed language defaults, basic docs, and standard commands.

It is intentionally not a product architect. Use it to create a deterministic starting repo, then add the domain model, APIs, security choices, and tests that belong to the product.

## Get Started

```bash
poetry install
make run
```

Create a service:

```bash
poetry run kickstart create service my-api --lang python
```

Create a Cloudflare Worker:

```bash
poetry run kickstart create service edge-api --lang typescript --runtime cloudflare-workers
```

Create a system root:

```bash
poetry run kickstart create system product-stack
```

Create a CLI:

```bash
poetry run kickstart create cli ops-tool --lang rust
```

Add Bun + Turbo workspace tooling when you want a TypeScript workspace at the system root:

```bash
poetry run kickstart create system product-stack --workspace-tooling bun-turbo
```

## What It Generates

- `service`: Python, TypeScript, Rust, C++, or Go backend service structure.
- `frontend`: React, TypeScript, Vite, and Bun frontend app.
- `lib`: Python or Rust library project.
- `cli`: Python, Rust, or TypeScript CLI project with modular command/client/model/operation boundaries and framework-native command adapters.
- `system`: language-neutral composition repo containing apps, services, libs, tools, infrastructure, docs, and agent metadata.

## Major Choices

- Preferred stack: Rust, TypeScript, Python, SQL, and C++.
- Go is supported as a tolerated service target; Python and Rust are the first-class library targets, and Python, Rust, and TypeScript are first-class CLI targets.
- CLI command adapters default to clap for Rust, Typer for Python, and oclif for TypeScript.
- Rust is the preferred CLI delivery target for single-binary distribution and performance; Python and TypeScript still use their own professional CLI conventions instead of copying Rust's file layout.
- Service execution models: containers by default, Cloudflare Workers when requested.
- Implemented service extensions are intentionally narrow: Python/FastAPI container services support Postgres, Redis, and JWT; Rust container services support Redis and JWT; TypeScript container services support Postgres.
- System provider targets: `multi`, `aws`, `gcp`, `cloudflare`, or `none`.
- System platform profiles: `kubernetes`, `cloudflare-workers`, or `hybrid`.
- System workspace tooling defaults to `none`; use `--workspace-tooling bun-turbo` for root `package.json`, Turbo, Bun, and shared TypeScript config.
- Dockerfiles are image artifacts; Helm and Kustomize are Kubernetes artifact styles; Wrangler is the Cloudflare Worker artifact path.
- Generated docs and `.kickstart/scaffold.json` are always created for agents and humans.
- Knowledge adapters default to `none`; use `--knowledge obsidian`, `--knowledge backstage`, or `--knowledge both` only for external metadata.
- `system` is the primary aggregate project type. Legacy `mono` and `monorepo` aliases remain for compatibility, but new docs and examples should use `system`.
- `cloudflare-workers` is the canonical runtime name. Singular Worker spellings are accepted as aliases.
- Cloudflare Containers are not implemented yet; they are reserved for a future scaffold.

## Common Commands

```bash
poetry run kickstart create service my-api --lang python --database postgres --cache redis --auth jwt
poetry run kickstart create service api-rs --lang rust --cache redis --auth jwt
poetry run kickstart create service api-ts --lang typescript --database postgres
poetry run kickstart create service edge-rs --lang rust --runtime cloudflare-workers
poetry run kickstart create frontend web
poetry run kickstart create lib core-lib --lang python
poetry run kickstart create cli ops-tool-py --lang python
poetry run kickstart create cli ops-tool --lang rust
poetry run kickstart create cli ops-tool-ts --lang typescript
poetry run kickstart create system platform --cloud aws --runtime kubernetes --knowledge none
poetry run kickstart create system web-platform --workspace-tooling bun-turbo
```

## More Docs

- [Human Guide](docs/human-guide.md): options, project types, and how to build on top.
- [Agent Guide](docs/agent-guide.md): compact, LLM-oriented generation contract.
- [Agent Map](AGENTS.md): repo-local map for agents modifying kickstart itself.
- [Scaffold Contract](docs/scaffold-contract.md): always-generated docs, metadata, and option vocabulary.
- [CLI Framework Research](docs/decisions/cli-framework-research.md): decision record for clap, Typer, and oclif defaults.
- [Local Evals](docs/evals.md): scaffold matrix and generated-project validation commands.
- [Contributing](docs/contributing.md): how humans should change the repo.
- [Agent Contributing](docs/agent-contributing.md): how agents should safely modify the repo.

## Development

```bash
make check
make package
make binary
```

kickstart supports Python `>=3.12,<3.15`. CI tests Python 3.12, 3.13, and 3.14 on Linux and macOS. Release builds attach Linux/macOS x64 and arm64 standalone binaries for each supported Python minor.

Current local eval evidence is tracked in [Local Evals](docs/evals.md). Reports are generated under `/private/tmp` or another scratch path and are not committed.
