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

- `runtime`: how code executes, for example `container`, `cloudflare-workers`, `cli`, or `library`.
- `deploy`: what deploy artifacts are emitted, for example `docker`, `docker+helm`, `kustomize`, `helm`, or `cloudflare-workers`.
- `cloud`: provider or infrastructure target, for example `none`, `aws`, `gcp`, `cloudflare`, or `multi`.
- `knowledge_adapter`: external knowledge integration metadata, for example `none`, `obsidian`, `backstage`, or `both`.

Cloudflare Workers can appear in both `runtime` and `deploy`: it changes the code execution model and the deploy artifact. It is not treated as a Docker/Kubernetes container.

`--knowledge` controls external adapters only. It does not control whether generated docs exist; docs are part of the baseline scaffold contract.
