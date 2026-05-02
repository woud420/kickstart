# Kickstart Website

Small single-page website served by a TypeScript Cloudflare Worker.

The source lives in this directory so copy, CSS, tests, and release behavior are reviewed like normal code. CI deploys it on major/minor release tags and injects the current release metadata without requiring a source edit for every release.

## Stack

- Cloudflare Workers
- Wrangler
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

Release deployment uses:

```bash
bun run prepare-release -- --version 0.4.0
bun run deploy:release
```

`prepare-release` writes `wrangler.release.toml`, which is ignored by git.
