# Scaffold Contract

kickstart generates a stable project map for humans and agents. The goal is not to finish the product architecture; it is to make the starting repo explicit, reviewable, and easy to extend.

## Always Generated

Every project type gets:

- `AGENTS.md`: short agent map for where to look first.
- `docs/architecture/`: structure, boundaries, and architecture notes.
- `docs/contracts/`: project-specific public surface. For a service this may be HTTP, env vars, ports, and queues; for a CLI it may be commands, flags, config files, and exit codes; for a library it may be public APIs and package metadata.
- `docs/operations/`: project-specific development, validation, packaging, deployment, and runbook notes.
- `docs/decisions/`: durable architecture and implementation decisions.
- `.kickstart/scaffold.json`: machine-readable scaffold metadata.
- `.github/workflows/ci.yml`: per-language GitHub Actions workflow that runs `make check` (lint + typecheck + tests) on push and pull requests. The workflow is emitted for every service, CLI, library, and frontend; system scaffolds emit `build.yml`, `test.yml`, and `deploy.yml` at the same path instead.

There is no separate root architecture document. `docs/architecture/` is the canonical architecture location.

## Option Vocabulary

- `project.kind`: what kickstart generated, for example `service`, `worker`, `frontend`, `library`, `cli`, or `system`.
- `project.repo_layout`: how generated projects are arranged, for example `single-project` or `monorepo`.
- `project.architecture`: optional named source layout profile, for example `modular-cli`.
- `project.cli_framework`: optional CLI framework selected by the language profile, for example `clap`, `typer`, or `oclif`.
- `project.command_root`: optional framework-native command adapter root.
- `project.entrypoint`: optional process entrypoint.
- `project.operation_root`: optional use-case implementation root.
- `project.src_root_files`: optional list of files expected directly under `src/`.
- `execution.models`: how code runs, for example `container`, `cloudflare-worker`, `static-site`, `cli`, or `library`.
- `execution.platforms`: where runtime artifacts are meant to run, for example `local`, `kubernetes`, `cloudflare-workers`, `static-host`, or `none`.
- `artifacts`: emitted files and tool configs, for example `image: dockerfile`, `kubernetes: kustomize`, `kubernetes: helm`, `worker: wrangler`, `iac: terraform`, or `ci: github-actions`.
- `provider.targets`: infrastructure providers targeted by generated IaC or platform config, for example `aws`, `gcp`, or `cloudflare`.
- `capabilities`: optional generated capabilities with real code support, for example `service_extensions: { database: postgres, cache: redis, auth: jwt }`.
- `composition.workspace_tooling`: system-only root workspace tooling, for example `none` or `bun-turbo`.
- `knowledge_adapter`: external knowledge integration metadata, for example `none`, `obsidian`, `backstage`, or `both`.

Implemented service extensions are intentionally narrow. Python/FastAPI container services support Postgres, Redis, and JWT. Rust container services support Redis and JWT. TypeScript container services support Postgres. Unsupported combinations fail instead of generating a partial or silent scaffold.

CLI scaffolds use `project.architecture: modular-cli` and align Rust, Python, and TypeScript around the same agent-facing boundaries: command adapters, config, clients, DTO/model, operations, output, and errors. Language idioms still apply: Rust uses `project.cli_framework: clap` with `project.command_root: src/cli`, Python uses `typer` with `src/cli/commands`, and TypeScript uses `oclif` with `src/commands` and `bin/run.js`.

Systems contain other project kinds and are generated through the `system` command with `project.repo_layout: monorepo`. A system is language-neutral by default. Use `--workspace-tooling bun-turbo` when the root should also be a Bun/Turbo TypeScript workspace. The older `mono` and `monorepo` project types remain backwards-compatible aliases that preserve the historical Bun/Turbo default, but new usage should prefer `system`.

Docker is an image/build artifact. Kubernetes is a runtime platform for containers. Helm and Kustomize are Kubernetes artifact styles. Cloudflare Workers are a Cloudflare runtime platform, not a Docker or Kubernetes container. Cloudflare Containers should be modeled separately as Worker-controlled container images when that scaffold is added.

Cloudflare Containers are reserved for future support and are not part of the current supported service runtime set.

`--knowledge` controls external adapters only. It does not control whether generated docs exist; docs are part of the baseline scaffold contract.
