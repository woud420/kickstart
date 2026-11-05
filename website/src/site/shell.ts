import type { ProjectMeta } from "./content";
import { escapeHtml } from "./format";
import { fontStylesheetUrl, siteTheme } from "./theme";

interface PageHead {
  title: string;
  description: string;
  styles?: readonly string[];
  links?: readonly { rel: string; href: string; type?: string }[];
  noindex?: boolean;
}

const favicon = `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="${siteTheme.ink}"/><path d="M9 7h4v18H9zM23 7h-4v18h4z" fill="${siteTheme.paper}"/><rect x="14.5" y="19" width="3" height="6" fill="${siteTheme.accent}"/></svg>`)}`;

export function renderPageHead(meta: ProjectMeta, page: PageHead): string {
  return `<meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(page.title)}</title>
    <meta name="description" content="${escapeHtml(page.description)}" />
    <meta name="theme-color" content="${siteTheme.paper}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="${escapeHtml(page.title)}" />
    <meta property="og:description" content="${escapeHtml(page.description)}" />
    ${page.noindex ? '<meta name="robots" content="noindex" />' : ""}
    <link rel="icon" href="${escapeHtml(favicon)}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="${escapeHtml(fontStylesheetUrl)}" rel="stylesheet" />
    ${["/assets/site.css", ...(page.styles ?? [])].map((path) => `<link rel="stylesheet" href="${escapeHtml(path)}?v=${escapeHtml(meta.latestVersion)}" />`).join("\n    ")}
    ${(page.links ?? []).map((link) => `<link rel="${escapeHtml(link.rel)}"${link.type ? ` type="${escapeHtml(link.type)}"` : ""} href="${escapeHtml(link.href)}" />`).join("\n    ")}`;
}

export function renderSiteHeader(meta: ProjectMeta, docs = false): string {
  const home = docs ? "/" : "";
  return `<a class="skip-link" href="#main">Skip to content</a>
    <header class="${docs ? "docs-shell" : "shell"} topbar">
      <div><a class="brand" href="/" aria-label="kickstart home">kickstart</a><span class="brand-version">v${escapeHtml(meta.latestVersion)}</span>${docs ? '<span class="docs-wordmark">/ docs</span>' : ""}</div>
      <nav aria-label="Main navigation">
        <a class="bracketed" href="/docs/get-started"${docs ? ' aria-current="location"' : ""}>docs</a>
        <a class="bracketed" href="${home}#examples">examples</a>
        <a class="bracketed" href="${home}#positioning">scope</a>
        <a class="bracketed" href="${home}#release">releases</a>
        <a class="bracketed" href="${escapeHtml(meta.repositoryUrl)}">github</a>
      </nav>
    </header>`;
}

export function renderCopyButton(target: string, label: string): string {
  return `<button class="copy" type="button" data-copy-target="${escapeHtml(target)}" aria-label="${escapeHtml(label)}">copy</button>`;
}

export function renderPageScripts(meta: ProjectMeta, examples = false): string {
  return `<p id="copy-status" class="visually-hidden" role="status" aria-live="polite"></p>
    <script src="/assets/${examples ? "site" : "copy"}.js?v=${escapeHtml(meta.latestVersion)}" type="module"></script>`;
}
