# kickstart website

The kickstart-cli.org landing page: one TypeScript Cloudflare Worker, deployed
with Alchemy v2 whenever a stable release is tagged.

## Commands

```bash
bun install
bun run dev     # local server
bun run check   # typecheck and tests
```

Copy, examples and release notes live in `src/site/content.ts`. The
[website-update skill](../.agents/skills/website-update/SKILL.md) lists the
tests that keep them accurate.

## Deploy

The release workflow runs `bun run deploy:release`
(`alchemy deploy --stage prod --adopt --yes`) for every stable tag. It needs:

- the `CLOUDFLARE_ACCOUNT_ID` repository variable;
- the `CLOUDFLARE_WEBSITE_API_TOKEN` secret, with `Workers Scripts: Write` on
  the account and `Zone: Read` on `kickstart-cli.org`.

Alchemy state is a local file, so each deploy adopts the existing Worker and
the `kickstart-cli.org` and `www` custom domains by name. Alchemy is pinned to
`2.0.0-beta.83` because v2 is still in beta. Zone hardening (SSL, HTTPS
redirects, bot protection) is set in the Cloudflare dashboard, not in
`alchemy.run.ts`.
