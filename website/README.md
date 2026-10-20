# kickstart website

Small single-page website served by a TypeScript Cloudflare Worker.

The source lives in this directory so copy, CSS, tests, and release behavior are reviewed like normal code. CI deploys it on stable release tags and injects the current release metadata without requiring a source edit for every release.

## Stack

- Cloudflare Workers
- Alchemy
- Wrangler for local Worker compatibility
- Bun
- Strict TypeScript
- Vitest

## Commands

```bash
bun install
bun run dev
bun run check
bun run deploy
```

Release deployment reads the package version from the repository `pyproject.toml` by default and deploys the production Worker through Alchemy:

```bash
bun run deploy:release
```

GitHub Actions requires the `CLOUDFLARE_WEBSITE_API_TOKEN` repository secret
and the `CLOUDFLARE_ACCOUNT_ID` repository variable before it will deploy the
website. Local deploys use your default Alchemy stage unless you pass `--stage`.

CI deploys run with `ALCHEMY_CI_STATE_STORE_CHECK=false` because the Worker and
its custom domain use `adopt: true` — every deploy converges on the same named
resources, so ephemeral runner state cannot orphan infrastructure. Setting the
optional `ALCHEMY_PASSWORD` and `ALCHEMY_STATE_TOKEN` repository secrets makes
`alchemy.run.ts` use the persistent Cloudflare state store instead.

Production deploys bind the Worker to `kickstart-cli.org` and
`www.kickstart-cli.org` through Alchemy; the Worker answers `www` with a 308
redirect to the apex, keeping path and query. The release workflow reads
`CLOUDFLARE_ACCOUNT_ID` from repository variables and
`CLOUDFLARE_WEBSITE_API_TOKEN` from repository secrets, then exposes them to
Alchemy as the Cloudflare environment variables it expects.

The Cloudflare token needs `Workers Scripts: Write` on the website's Cloudflare
account. It also needs a domain-scoped policy for `kickstart-cli.org` with
`Zone: Read` so Alchemy can infer the zone for the custom domain bindings. The
`www.kickstart-cli.org` custom domain lives in the same zone, so those zone
permissions cover it too; no extra token scope is needed.
`Workers Routes: Edit` is only needed if the website switches from a Worker
custom domain to route-pattern deployment.

Zone security settings (SSL strict, Always Use HTTPS, Automatic HTTPS
Rewrites, Bot Fight Mode, AI bot blocking) are declared in `alchemy.run.ts`
but are not applied by release deploys, because they need much broader
rights than the release token should hold. Alchemy's `Zone` resource
creates-or-adopts the zone, which needs account-wide `Zone: Edit`, plus
`Zone Settings: Edit` and `Bot Management: Edit` on `kickstart-cli.org`. To
apply or change them, deploy once from a trusted machine with a token that
has those rights:

```bash
KICKSTART_MANAGE_ZONE=1 CLOUDFLARE_API_TOKEN=<operator token> bun run deploy:release
```
