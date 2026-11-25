# kickstart website

The kickstart-cli.org landing page and docs: one TypeScript Cloudflare Worker, deployed
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

## Documentation

`/docs` redirects to `/docs/get-started`. Pages are rendered on the server with
grouped navigation, page outlines, copyable examples, and a native mobile menu.
Unknown `/docs/` paths return a documentation 404; existing landing-page routes
keep their current behavior.

`src/docs/content.ts` is the typed public documentation source. It contains
sections and explicit paragraph, code, list, table, note, and link blocks;
`src/docs/html.ts` renders them without a Markdown parser or client framework.
Source notes link back to the repository contracts and runbooks. Keep product
claims aligned with those sources and the supported release. Search is deferred
for this first documentation release; every page is accessible through navigation.

Landing pages and documentation share `src/site/theme.ts` and `src/site/shell.ts`:
Fraunces display headings, Atkinson Hyperlegible prose, IBM Plex Mono code/UI,
the paper/red palette, head metadata, favicon, header, and copy controls. Shared
copy behavior lives in `src/assets/copy-script.ts`; docs load that small asset
without the landing page's example-tab payload.

The same registry also produces `/llms.txt` (a concise Markdown index),
`/llms-full.txt` (all nine public pages), and `/docs/<slug>.md` (one clean page).
`src/docs/markdown.ts` renders those on demand, so there are no generated text
copies to refresh or commit. The inclusion list is exactly the public page
registry, not every repository document. HTML declares Markdown alternates and
the llms.txt discovery link. Text responses use UTF-8 `text/plain`, absolute
canonical URLs, and release metadata from the same Worker configuration as HTML.

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

## Deployment verification

The public site remains on `kickstart-cli.org` with Bot Fight Mode enabled.
The `workers.dev` hostname is not a second public website: all routes return
404 except an authenticated `GET /healthz`. Version preview URLs are disabled;
the handler also applies the same restrictions to any preview hostname.

Before deploying, release CI generates a random 256-bit bearer token and masks
it in the job log. Only its SHA-256 digest and a 15-minute expiry are bound to
the Worker. No permanent repository secret is needed. Missing or expired
configuration fails closed, including local/manual remote deployments without
the probe environment. The token allows only health metadata, never HTML or
assets, and each deployment replaces its digest. Old versions created before
this restriction must not be re-enabled as public previews.

CI checks `https://kickstart-site.polarcoordinates.workers.dev/healthz` for
the expected version, service and status, with five attempts and a ten-second
timeout per request. Redirects are rejected so the credential stays on the
Worker endpoint. The production deploy job is serialized so another release
cannot replace the credential between deployment and verification.
If the Worker name or account subdomain changes, update
`scripts/verify-deployment.ts` too.

This proves the deployed Worker responds; it does not prove custom-domain
DNS, TLS or bot-policy behavior. Check the public site and its `/healthz`
version manually in a browser after a release. Renaming the health path does
not avoid domain-wide Bot Fight Mode. The historical v0.4.6 workflow remains
failed; this check applies after the PR is merged and deployed.
