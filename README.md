# kickstart

kickstart is a scaffolding tool for generating project structure, services, workers, frontends, libraries, CLIs, and systems.

The goal is to eliminate the repeated setup work that humans and agents otherwise redo at the start of every project: directories, templates, Docker/Kubernetes/Cloudflare files, typed language defaults, basic docs, and standard commands.

It is intentionally not a product architect. Use it to create a deterministic starting repo, then add the domain model, APIs, security choices, and tests that belong to the product.

Release history lives in [CHANGELOG.md](CHANGELOG.md) and on [kickstart-cli.org](https://kickstart-cli.org).

## Install

One-line install of the latest release. Drops a launcher in `~/.local/bin/kickstart` and the binary payload in `~/.local/share/kickstart` (Linux x64/arm64 and macOS arm64; other platforms install from PyPI with `pip install kickstart`):

```bash
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash
```

The script downloads the matching binary archive for your platform from a GitHub release, verifies its SHA-256 checksum, extracts it under the binary directory, and offers to append a managed `PATH` block to your shell rc file. Knobs:

```bash
# Install into /usr/local without touching shell rc files. Picks /usr/local/share/kickstart
# for the binary payload automatically.
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh \
  | KICKSTART_INSTALL_DIR=/usr/local/bin bash -s -- --no-path-update

# Pin a specific release tag (replace v<TAG> with one from the Releases page).
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh \
  | KICKSTART_VERSION=v<TAG> bash
```

Already pulled the binary archive from the Releases page? Extract it and use kickstart's own installer to lay out the launcher and configure `PATH`:

```bash
tar -xzf kickstart-macos-arm64-py3.14.tar.gz
./kickstart-macos-arm64-py3.14/kickstart install --update-path
# Drops a symlink at ~/.local/bin/kickstart pointing at ~/.local/share/kickstart/current/kickstart
# and edits ~/.zshrc, ~/.bash_profile, or ~/.config/fish/config.fish.

./kickstart-macos-arm64-py3.14/kickstart install --target /usr/local/bin --app-dir /usr/local/share/kickstart
./kickstart-macos-arm64-py3.14/kickstart install --check                    # just report install/PATH status
./kickstart-macos-arm64-py3.14/kickstart install --force                    # overwrite an existing install
./kickstart-macos-arm64-py3.14/kickstart install --shell bash               # override $SHELL detection
./kickstart-macos-arm64-py3.14/kickstart uninstall --clean-path             # remove launcher + binary payload, restore rc file
```

Refresh in place against the newest release once installed:

```bash
kickstart upgrade
```

Or install from PyPI when published:

```bash
pip install kickstart
```

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

Check an existing repo against the scaffold standard (read-only; exit 0 = matches, 1 = gaps, 2 = usage error):

```bash
poetry run kickstart adopt path/to/repo --check          # human report
poetry run kickstart adopt path/to/repo --check --json   # machine-readable, for agents and CI
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

kickstart supports Python `>=3.12,<3.15`. CI tests Python 3.12, 3.13, and 3.14 on Linux and macOS. Release builds attach Linux/macOS x64 and arm64 binary archives (`kickstart-<platform>-py<minor>.tar.gz`) for each supported Python minor.

Current local eval evidence is tracked in [Local Evals](docs/evals.md). Reports are generated under `/tmp` or another scratch path and are not committed.
