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

Production deploys bind the Worker to `kickstart-cli.org` through Alchemy. The
release workflow reads `CLOUDFLARE_ACCOUNT_ID` from repository variables and
`CLOUDFLARE_WEBSITE_API_TOKEN` from repository secrets, then exposes them to
Alchemy as the Cloudflare environment variables it expects.

The Cloudflare token needs an account-scoped policy for the `polarcoordinates`
account with `Workers Scripts: Write`. It also needs a domain-scoped policy for
`kickstart-cli.org` with `Zone: Read` so Alchemy can infer the zone for the
custom domain binding. `Workers Routes: Edit` is only needed if the website
switches from a Worker custom domain to route-pattern deployment.
