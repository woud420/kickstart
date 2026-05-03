# Operations

## Lifecycle flow
1. Install dependencies: `make install`
2. Verify scaffold contract: `make check`
3. Run local worker runtime: `make dev`
4. Deploy to Cloudflare Workers: `make deploy`

## Verification files
- `Makefile` contains lifecycle command wrappers.
- `docs/contracts/README.md` describes runtime and handler constraints.
- `.kickstart/scaffold.json` records command and platform metadata.

## Deploy assumptions
- Wrangler authentication is available.
- Required bindings and secrets are configured before deploy.
- Deployment target details live in `wrangler.toml`.
