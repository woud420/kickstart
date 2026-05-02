# ADR 0001: Application Workspace Stack

## Status

Accepted for initial scaffold.

## Context

This workspace starts from a polyglot application shape: Python, Rust, and C++ for services and tooling, TypeScript for user-facing and edge code, SQL for durable data contracts, Docker for local parity, and Terraform for cloud resources.

TypeScript workspaces use Bun for package/runtime workflow and Turbo for task orchestration. Generated directories separate deployable `apps/`, reusable `packages/`, service runtimes, shared `config/`, and durable `knowledge/`.

{% if uses_kubernetes and uses_cloudflare_workers -%}
The scaffold targets {{ cloud_label }} with Kubernetes manifests for long-running services and Cloudflare Workers for edge runtime paths. Deployment-oriented commands use {{ deployment_tool }}.
{% elif uses_kubernetes -%}
The scaffold targets {{ cloud_label }} and uses {{ deployment_tool }} for Kubernetes packaging.
{% else -%}
The scaffold targets {{ cloud_label }} and uses {{ deployment_tool }} for Cloudflare Worker runtime notes and deploy intent.
{% endif -%}
{% if include_cloudflare or uses_cloudflare_workers %}
Cloudflare support covers DNS, Workers, routes, tunnels, and access-policy scaffolding when those resources are part of the selected profile.
{% endif %}

## Decision

- Use PostgreSQL as the default relational store.
- Use Redis as the default local cache.
- Use Docker Compose for local dependency orchestration.
- Use Terraform environment folders for cloud-specific infrastructure.
{% if uses_kubernetes -%}
- Use Kubernetes manifests for runtime deployment.
{% endif -%}
{% if uses_cloudflare_workers -%}
- Use Cloudflare Worker notes and Wrangler examples for edge runtime deployment.
{% endif %}

Knowledge artifacts live in Markdown-first docs so they can be read directly, opened as an Obsidian vault{% if include_obsidian %}, and linked into Obsidian{% endif %}{% if include_backstage %}, while `catalog-info.yaml` makes the workspace discoverable in Backstage{% endif %}.

## Consequences

- Service teams get a runnable local stack before cloud resources exist.
- Infrastructure code has clear dev, staging, and prod entrypoints.
- Generated projects start with review paths for data modeling, security, architecture, and external interface mapping.
- Cloud resources are intentionally stubs until application-specific requirements are known.
