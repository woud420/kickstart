# Human Guide

Kickstart creates project scaffolds so the first hour of setup is repeatable instead of hand-built.

## Project Types

| Type | Command | Use For |
| --- | --- | --- |
| Service | `kickstart create service NAME --lang python` | Backend APIs and microservices |
| Frontend | `kickstart create frontend NAME` | React/Vite/Bun apps |
| Library | `kickstart create lib NAME --lang python` | Reusable packages |
| CLI | `kickstart create cli NAME --lang rust` | Command-line tools |
| Monorepo | `kickstart create mono NAME` | TypeScript workspace plus infrastructure |

## Service Options

Languages:

- `python`: FastAPI by default, or `--framework minimal`
- `typescript` or `ts`: Bun + Fastify
- `rust`: Actix-web
- `cpp`: C++20 + CMake
- `go`: minimal `net/http`

Runtime:

- `container`: default service runtime
- `cloudflare-workers`: TypeScript or Rust Worker scaffold

Python extensions:

- `--database postgres`
- `--cache redis`
- `--auth jwt`

## Library And CLI Options

Python and Rust are the first-class library and CLI targets. Other language templates may exist, but should be treated as thinner scaffolds unless the generated output has explicit coverage.

## Monorepo Options

Cloud profile:

- `multi`: AWS, GCP, and Cloudflare entrypoints
- `aws`, `gcp`, `cloudflare`: provider-specific entrypoints
- `none`: no cloud provider assumptions

Runtime profile:

- `kubernetes`: Kustomize by default, Helm with `--helm`
- `cloudflare-workers`: Wrangler-oriented Worker runtime notes
- `hybrid`: Kubernetes plus Cloudflare Workers

Knowledge profile:

- `none`: default; no Backstage or Obsidian metadata
- `obsidian`: adds Obsidian vault settings
- `backstage`: adds Backstage catalog/template files
- `both`: adds both knowledge-system integrations

## Building On Top

Prefer extending the typed plan layers before adding generator branches:

- Directory plans live in `src/generator/layouts.py`.
- Template plans live in `src/generator/template_plans.py`.
- Service language setup plans live in `src/generator/language_setup.py`.
- Stack choices live in `src/stack/`.

When adding a new scaffold option, add generated-output tests for the affected project type before refactoring that path.

## Project Tooling

Kickstart supports Python `>=3.12,<3.15`. Use `make check` before committing. Use `make package` for wheel/source builds and `make binary` for a local standalone binary.
