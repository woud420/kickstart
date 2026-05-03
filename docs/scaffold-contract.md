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

There is no separate root architecture document. `docs/architecture/` is the canonical architecture location.

## Option Vocabulary

- `project.kind`: what kickstart generated, for example `service`, `worker`, `frontend`, `library`, `cli`, or `system`.
- `project.repo_layout`: how generated projects are arranged, for example `single-project` or `monorepo`.
- `execution.models`: how code runs, for example `container`, `cloudflare-worker`, `cloudflare-container`, `static-site`, `cli`, or `library`.
- `execution.platforms`: where runtime artifacts are meant to run, for example `local`, `kubernetes`, `cloudflare-workers`, `cloudflare-containers`, `static-host`, or `none`.
- `artifacts`: emitted files and tool configs, for example `image: dockerfile`, `kubernetes: kustomize`, `kubernetes: helm`, `worker: wrangler`, `iac: terraform`, or `ci: github-actions`.
- `provider.targets`: infrastructure providers targeted by generated IaC or platform config, for example `aws`, `gcp`, or `cloudflare`.
- `capabilities`: optional generated capabilities with real code support, for example `service_extensions: { database: postgres, cache: redis, auth: jwt }`.
- `knowledge_adapter`: external knowledge integration metadata, for example `none`, `obsidian`, `backstage`, or `both`.

Implemented service extensions are intentionally narrow. Python/FastAPI container services support Postgres, Redis, and JWT. Rust container services support Redis and JWT. TypeScript container services support Postgres. Unsupported combinations fail instead of generating a partial or silent scaffold.

Systems contain other project kinds and are currently generated through the `mono` command with `project.repo_layout: monorepo`.

Docker is an image/build artifact. Kubernetes is a runtime platform for containers. Helm and Kustomize are Kubernetes artifact styles. Cloudflare Workers are a Cloudflare runtime platform, not a Docker or Kubernetes container. Cloudflare Containers are modeled separately as Worker-controlled container images when that scaffold is added.

`--knowledge` controls external adapters only. It does not control whether generated docs exist; docs are part of the baseline scaffold contract.
