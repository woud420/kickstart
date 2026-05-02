# ADR 0001: Application Workspace Stack

## Status

Accepted for initial scaffold.

## Context

This workspace starts from a polyglot application shape: Python, Rust, and C++ for services and tooling, TypeScript for user-facing and edge code, SQL for durable data contracts, Docker for local parity, Kubernetes for deployment, and Terraform for cloud resources.

TypeScript workspaces use Bun for package/runtime workflow and Turbo for task orchestration. Generated directories separate deployable `apps/`, reusable `packages/`, service runtimes, shared `config/`, and durable `knowledge/`.

The scaffold targets {{ cloud_label }} and uses {{ deployment_tool }} for Kubernetes packaging. Cloudflare is modeled as an edge/cloud provider for DNS, Workers, routes, tunnels, and access policies rather than as a replacement for local Docker or Kubernetes defaults.

## Decision

Use PostgreSQL as the default relational store, Redis as the default local cache, Docker Compose for local dependency orchestration, Kubernetes manifests for runtime deployment, and Terraform environment folders for cloud-specific infrastructure.

Knowledge artifacts live in Markdown-first docs so they can be read directly, opened as an Obsidian vault{% if include_obsidian %}, and linked into Obsidian{% endif %}{% if include_backstage %}, while `catalog-info.yaml` makes the workspace discoverable in Backstage{% endif %}.

## Consequences

- Service teams get a runnable local stack before cloud resources exist.
- Infrastructure code has clear dev, staging, and prod entrypoints.
- Generated projects start with review paths for data modeling, security, architecture, and external interface mapping.
- Cloud resources are intentionally stubs until application-specific requirements are known.
