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

GitHub Actions requires `ALCHEMY_PASSWORD`, `ALCHEMY_STATE_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `CLOUDFLARE_API_TOKEN` before it will deploy the website. Local deploys use your default Alchemy stage unless you pass `--stage`.
