# kickstart

kickstart is a scaffolding tool for generating project structure, CLIs, services, frontends, libraries, and infrastructure workspaces.

The goal is to eliminate the repeated setup work that humans and agents otherwise redo at the start of every project: directories, templates, Docker/Kubernetes/Cloudflare files, typed language defaults, basic docs, and standard commands.

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

Create a TypeScript infrastructure monorepo:

```bash
poetry run kickstart create mono product-stack
```

## What It Generates

- `service`: Python, TypeScript, Rust, C++, or Go backend service structure.
- `frontend`: React, TypeScript, Vite, and Bun frontend app.
- `lib`: Python or Rust library project.
- `cli`: Python or Rust CLI project.
- `mono`: TypeScript/Bun/Turbo workspace with infrastructure, docs, and optional cloud/runtime profiles.

## Major Choices

- Preferred stack: Rust, TypeScript, Python, SQL, and C++.
- Go is supported as a tolerated service target; Python and Rust are the first-class library/CLI targets.
- Service runtimes: containers by default, Cloudflare Workers when requested.
- Monorepo cloud targets: `multi`, `aws`, `gcp`, `cloudflare`, or `none`.
- Monorepo runtime targets: `kubernetes`, `cloudflare-workers`, or `hybrid`.
- Knowledge systems default to `none`; use `--knowledge obsidian`, `--knowledge backstage`, or `--knowledge both` only when wanted.

## Common Commands

```bash
poetry run kickstart create service my-api --lang python --database postgres --cache redis --auth jwt
poetry run kickstart create service api-rs --lang rust
poetry run kickstart create service edge-rs --lang rust --runtime cloudflare-workers
poetry run kickstart create frontend web
poetry run kickstart create lib core-lib --lang python
poetry run kickstart create cli ops-tool --lang rust
poetry run kickstart create mono platform --cloud aws --runtime kubernetes --knowledge none
```

## More Docs

- [Human Guide](docs/human-guide.md): options, project types, and how to build on top.
- [Agent Guide](docs/agent-guide.md): compact, LLM-oriented generation contract.
- [Contributing](docs/contributing.md): how humans should change the repo.
- [Agent Contributing](docs/agent-contributing.md): how agents should safely modify the repo.

## Development

```bash
make check
make package
make binary
```

kickstart supports Python `>=3.12,<3.15`. CI tests Python 3.12, 3.13, and 3.14 on Linux and macOS. Release builds attach Linux/macOS x64 and arm64 standalone binaries for each supported Python minor.
