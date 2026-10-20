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

`alchemy.run.ts` is an Alchemy v2 stack (`alchemy@2.0.0-beta.83`, Effect 4),
pinned exactly because v2 is still in beta. It keeps state in a local file
(`.alchemy/`). CI runners start empty, so `bun run deploy:release` runs
`alchemy deploy --stage prod --adopt --yes`: every deploy adopts the existing
Worker and custom domains by name, so ephemeral state cannot orphan
infrastructure. Alchemy's remote `Cloudflare.state()` store would need a
bootstrapped state-store Worker and `Secrets Store: Write` on the token, so it
is not used.

Production deploys bind the Worker to `kickstart-cli.org` and
`www.kickstart-cli.org` through Alchemy; the Worker answers `www` with a 308
redirect to the apex, keeping path and query. The release workflow reads `CLOUDFLARE_ACCOUNT_ID` from repository variables and
`CLOUDFLARE_WEBSITE_API_TOKEN` from repository secrets, then exposes them to
Alchemy as the Cloudflare environment variables it expects.

The Cloudflare token needs `Workers Scripts: Write` on the website's Cloudflare
account. It also needs a domain-scoped policy for `kickstart-cli.org` with
`Zone: Read` so Alchemy can infer the zone for the custom domain bindings. The
`www.kickstart-cli.org` custom domain lives in the same zone, so those zone
permissions cover it too; no extra token scope is needed.
`Workers Routes: Edit` is only needed if the website switches from a Worker
custom domain to route-pattern deployment.

Zone hardening is managed in the Cloudflare dashboard, not by Alchemy. That
covers strict SSL, Always Use HTTPS, automatic HTTPS rewrites, Bot Fight Mode,
AI bot blocking and crawler protection on `kickstart-cli.org`. The v1 stack
asserted these settings on every deploy, which needs `Zone: Edit`,
`Zone Settings: Edit` and `Bot Management: Edit` on the release token.
Without those scopes that step stops the deploy before the Worker is updated.
