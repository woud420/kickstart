<!-- kickstart:begin agent-map -->
# Agent Map

## Scope
- This scaffold is an explicit TypeScript Cloudflare Worker contract.
- The docs below are the orientation surface; `.kickstart/scaffold.json` records the contract as machine-readable scaffold state for tooling.

## Code, tests, and config
- Worker code: `src/index.ts`
- Contract tests: `tests/worker.test.ts`
- Runtime config: `wrangler.toml`
- Tooling config: `package.json`, `tsconfig.json`, `Makefile`
- Local env template: `.dev.vars.example` (copy to `.dev.vars` for local secrets)

## Commands
- Verify contract: `make check`
- Local development: `make dev`
- Deploy: `make deploy`

## Deploy assumptions
- Wrangler is authenticated (`wrangler login` locally or `CLOUDFLARE_API_TOKEN` in CI).
- Cloudflare bindings and secrets are configured before `make deploy`.
- Keep `SERVICE_NAME` bindings aligned between `wrangler.toml`, `.dev.vars`, and tests.

## Do not hand-edit generated contract files
- `.kickstart/scaffold.json`
- `AGENTS.md`
- `docs/contracts/README.md`
- `docs/operations/README.md`

Regenerate with kickstart when scaffold conventions change.
<!-- kickstart:end agent-map -->
