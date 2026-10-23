import { defaultProjectMeta, type ProjectMeta } from "../site/content";
import { escapeHtml, formatCommand } from "../site/format";
import { docGroups, docPath, documentationPages, type DocBlock, type DocPage } from "./content";
import { renderCopyButton, renderPageHead, renderPageScripts, renderSiteHeader } from "../site/shell";

function inline(text: string): string {
  return text.split("`").map((part, index) => index % 2 ? `<code>${escapeHtml(part)}</code>` : escapeHtml(part)).join("");
}

function navigation(current?: DocPage): string {
  return `<nav class="docs-nav" aria-label="Documentation">${docGroups.map((group) => `
    <div class="docs-nav-group"><p class="docs-nav-label">${group}</p>
      ${documentationPages.filter((page) => page.group === group).map((page) =>
        `<a href="${docPath(page)}"${page === current ? ' aria-current="page"' : ""}>${page.slug === "get-started" ? "Get started" : escapeHtml(page.title)}</a>`).join("")}
    </div>`).join("")}</nav>`;
}

function blockHtml(block: DocBlock, id: string): string {
  switch (block.kind) {
    case "paragraph": return `<p>${inline(block.text)}</p>`;
    case "code": {
      const display = block.value.split("\n").map((line) => {
        if (line.startsWith("kickstart create ") && !line.endsWith(" --help")) return formatCommand(line);
        if (line.startsWith("curl ") && line.length > 85) return line.replace(" https:", " \\\n  https:").replace(" | ", " \\\n  | ");
        return line;
      }).join("\n");
      return `<div class="docs-code"><div class="docs-code-head"><span>${escapeHtml(block.label)}</span>${renderCopyButton(id, `Copy ${block.label.toLowerCase()}`)}</div><pre><code id="${id}" data-copy="${escapeHtml(block.value)}">${escapeHtml(display)}</code></pre></div>`;
    }
    case "list": return `<ul>${block.items.map((item) => `<li>${inline(item)}</li>`).join("")}</ul>`;
    case "table": return `<div class="docs-table" role="region" aria-label="${escapeHtml(block.headers.join(", "))}" tabindex="0"><table><thead><tr>${block.headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr></thead><tbody>${block.rows.map((row) => `<tr>${row.map((cell) => `<td>${inline(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    case "note": return `<aside class="docs-note"><p class="docs-note-title">${escapeHtml(block.title)}</p><p>${inline(block.text)}</p></aside>`;
    case "links": return `<ul class="docs-links">${block.items.map((item) => `<li><a href="${escapeHtml(item.href)}">${escapeHtml(item.title)} <span aria-hidden="true">↗</span></a><p>${escapeHtml(item.description)}</p></li>`).join("")}</ul>`;
  }
}

function pageFrame(title: string, summary: string, body: string, meta: ProjectMeta, page?: DocPage): string {
  const nav = navigation(page);
  return `<!doctype html>
<html lang="en">
<head>
  ${renderPageHead(meta, {
    title: `${title} · kickstart docs`,
    description: summary,
    styles: ["/assets/docs.css"],
    links: page ? [{ rel: "canonical", href: `https://kickstart-cli.org${docPath(page)}` }] : [],
    noindex: !page,
  })}
</head>
<body class="docs-body">
  ${renderSiteHeader(meta, true)}
  <div class="docs-shell docs-layout">
    <aside class="docs-sidebar">${nav}<a class="docs-source-link" href="${escapeHtml(meta.releaseUrl)}">Release notes ↗</a></aside>
    <details class="docs-menu"><summary>Browse documentation</summary>${nav}</details>
    <main class="docs-article" id="main" tabindex="-1">${body}</main>
    ${page ? `<aside class="docs-outline"><nav aria-label="On this page"><p class="docs-nav-label">On this page</p>${page.sections.map((section) => `<a href="#${section.id}">${escapeHtml(section.title)}</a>`).join("")}</nav><p class="docs-outline-note">A repeatable start.<br />Your decisions from here.</p></aside>` : ""}
  </div>
  ${renderPageScripts(meta)}
</body>
</html>`;
}

export function renderDocHtml(page: DocPage, meta: ProjectMeta = defaultProjectMeta): string {
  const index = documentationPages.indexOf(page);
  const previous = documentationPages[index - 1];
  const next = documentationPages[index + 1];
  const body = `<header class="docs-heading"><p class="docs-eyebrow">Documentation <span>/</span> ${page.group}</p><h1>${escapeHtml(page.title)}</h1><p class="docs-lead">${escapeHtml(page.summary)}</p></header>
    ${page.sections.map((section, index) => `<section id="${section.id}" class="docs-section" aria-labelledby="heading-${section.id}"><h2 id="heading-${section.id}"><a href="#${section.id}">${escapeHtml(section.title)}</a></h2>${section.blocks.map((block, blockIndex) => blockHtml(block, `code-${index}-${blockIndex}`)).join("\n")}</section>`).join("\n")}
    <footer class="docs-footer"><p>Source notes</p><ul>${page.sources.map((source) => `<li><a href="${escapeHtml(meta.repositoryUrl)}/blob/master/${escapeHtml(source)}">${escapeHtml(source)}</a></li>`).join("")}</ul></footer>
    <nav class="docs-pager" aria-label="Previous and next pages">${previous ? `<a href="${docPath(previous)}"><span>← Previous</span>${escapeHtml(previous.slug === "get-started" ? "Get started" : previous.title)}</a>` : "<span></span>"}${next ? `<a href="${docPath(next)}"><span>Next →</span>${escapeHtml(next.title)}</a>` : ""}</nav>`;
  return pageFrame(page.title, page.summary, body, meta, page);
}

export function renderDocNotFound(meta: ProjectMeta = defaultProjectMeta): string {
  return pageFrame("Page not found", "This documentation page does not exist.", `<header class="docs-heading"><p class="docs-eyebrow">Documentation / 404</p><h1>Page not found</h1><p class="docs-lead">That documentation page does not exist.</p></header><p><a href="/docs/get-started">Start with the get-started guide →</a></p>`, meta);
}
