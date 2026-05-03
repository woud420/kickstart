# Contracts

## Scaffold identity
- Kind: `worker`
- Execution model: `cloudflare-worker`
- Runtime platform: `cloudflare-workers`
- Artifact: `wrangler`
- Provider target: `cloudflare`

See `.kickstart/scaffold.json` for the machine-readable source of truth.

## TypeScript Worker handler contract
- `src/index.ts` exports `default` and satisfies `ExportedHandler<Env>`.
- `Env` bindings in TypeScript are mirrored in `wrangler.toml` and `.dev.vars`.
- `/healthz` returns JSON health output and stays covered by tests.

## Verification contract
- Run `make check` before handoff.
- `make check` runs `make typecheck` and `make test`.
- `tests/worker.test.ts` validates the generated handler behavior.
