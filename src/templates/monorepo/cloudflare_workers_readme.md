# Cloudflare Workers Runtime

This workspace treats Cloudflare Workers as a runtime target, separate from Terraform cloud-provider resources.

## Responsibilities

- Worker projects own `wrangler.toml` and deploy through Wrangler.
- Terraform may own account-level resources such as DNS records, routes, Access policy, KV namespaces, D1 databases, R2 buckets, and Queues.
- `CLOUDFLARE_API_TOKEN` should be provided through local shell configuration or CI secrets.

## Suggested Layout

- `services/<worker-name>/` - generated Worker service
- `infra/cloudflare/workers/` - shared runtime notes and route examples
- `infra/terraform/env/<env>/` - account resources and bindings that should be versioned as infrastructure

Generate a Worker service with:

```bash
kickstart create service edge-api --lang typescript --runtime cloudflare-workers
kickstart create service edge-rust --lang rust --runtime cloudflare-workers
```
