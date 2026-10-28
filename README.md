# kickstart

[![CI](https://github.com/woud420/kickstart/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/woud420/kickstart/actions/workflows/ci.yml)
[![Release](https://github.com/woud420/kickstart/actions/workflows/release.yml/badge.svg)](https://github.com/woud420/kickstart/actions/workflows/release.yml)
[![Scheduled Evals](https://github.com/woud420/kickstart/actions/workflows/scheduled-evals.yml/badge.svg)](https://github.com/woud420/kickstart/actions/workflows/scheduled-evals.yml)
[![codecov](https://codecov.io/gh/woud420/kickstart/branch/master/graph/badge.svg)](https://codecov.io/gh/woud420/kickstart)
[![GitHub release](https://img.shields.io/github/v/release/woud420/kickstart)](https://github.com/woud420/kickstart/releases/latest)

kickstart generates starter repos for services, frontends, libraries, CLIs and
multi-project systems. Each one comes with its layout, typed language defaults,
Docker, Kubernetes or Cloudflare files, standard `make` targets, docs, and an
`AGENTS.md` that coding agents can follow.

It is not a product architect. It gives you a deterministic starting repo; the
domain model, APIs and tests are yours to add.

## Install

With Homebrew on macOS arm64 or Linux x64/arm64:

```bash
brew install woud420/tap/kickstart
```

Use `brew upgrade woud420/tap/kickstart` to update and
`brew uninstall woud420/tap/kickstart` to remove it. See the
[Homebrew runbook](docs/operations/homebrew.md) for platform requirements and
migrating an existing installation.

Or use the standalone installer:

```bash
curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash
```

This installs a SHA-256-verified binary to `~/.local/bin/kickstart` on Linux
(x64, arm64) and macOS (arm64). Elsewhere, use
`pipx install git+https://github.com/woud420/kickstart`; the PyPI package named
`kickstart` is an unrelated project. Update standalone installations with
`kickstart upgrade`.

Release builds send pseudonymous usage telemetry by default.
`kickstart telemetry disable` turns it off. The
[install runbook](docs/operations/install-binaries.md) covers custom paths and
uninstalling, and the [telemetry contract](docs/contracts/telemetry.md) lists
exactly what is sent.

## Quick start

```bash
kickstart create service api --lang python --database postgres --auth jwt
kickstart create service edge --lang typescript --runtime cloudflare-workers
kickstart create cli ops-tool --lang rust
kickstart create system platform --cloud aws --runtime kubernetes
kickstart adopt path/to/repo --check   # check an existing repo against the standard
```

For Python, Postgres and JWT add independent database and token/password helpers.
The example `/users` routes still use in-memory storage; signup, login, credential
persistence, and route protection are application work. See the
[Python Postgres/JWT contract](docs/contracts/python-postgres-jwt.md).

## What it generates

- `service`: Python, TypeScript, Rust, C++ or Go backend. TypeScript and Rust can also target Cloudflare Workers.
- `frontend`: React, TypeScript, Vite and Bun app.
- `lib`: Python or Rust library.
- `cli`: Python, Rust or TypeScript CLI.
- `system`: language-neutral repo for apps, services, libs, tools and infrastructure.

Every project also gets `AGENTS.md`, `CLAUDE.md`, `docs/` and
`.kickstart/scaffold.json`.

## Docs

- [Human guide](docs/human-guide.md): every option, and the inspection commands
  (`adopt`, `drift`, `plan`, `export`, `migrate`).
- [Agent guide](docs/agent-guide.md): the compact generation contract for agents.
- [Scaffold contract](docs/scaffold-contract.md): what every project always gets.
- [Changelog](CHANGELOG.md), also on [kickstart-cli.org](https://kickstart-cli.org).

## Development

```bash
poetry install
make check
```

Supports Python 3.12 to 3.14. [AGENTS.md](AGENTS.md) maps the repo, and
[contributing](docs/contributing.md) covers how to change it.
