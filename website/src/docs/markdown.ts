import { defaultProjectMeta, type ProjectMeta } from "../site/content";
import { docGroups, docPath, documentationPages, findDocPage, type DocBlock, type DocPage } from "./content";

export const docsOrigin = "https://kickstart-cli.org";

export function markdownPath(page: DocPage): string {
  return `${docPath(page)}.md`;
}

function textLink(href: string): string {
  const url = new URL(href, docsOrigin);
  if (url.origin === docsOrigin && url.pathname.startsWith("/docs/")) {
    const page = findDocPage(url.pathname.slice("/docs/".length));
    if (page) url.pathname = markdownPath(page);
  }
  return url.toString();
}

function tableCell(value: string): string {
  return value.replaceAll("|", "\\|").replaceAll("\n", " ");
}

function blockMarkdown(block: DocBlock): string {
  switch (block.kind) {
    case "paragraph": return block.text;
    case "code": {
      const longestRun = Math.max(0, ...Array.from(block.value.matchAll(/`+/g), (match) => match[0].length));
      const fence = "`".repeat(Math.max(3, longestRun + 1));
      return `${fence}${block.language}\n${block.value}\n${fence}`;
    }
    case "list": return block.items.map((item) => `- ${item}`).join("\n");
    case "table": return [block.headers, block.headers.map(() => "---"), ...block.rows]
      .map((row) => `| ${row.map(tableCell).join(" | ")} |`).join("\n");
    case "note": return `> **${block.title}**\n>\n> ${block.text}`;
    case "links": return block.items.map((item) => `- [${item.title}](${textLink(item.href)}): ${item.description}`).join("\n");
  }
}

export function renderDocMarkdown(page: DocPage, meta: ProjectMeta = defaultProjectMeta): string {
  return [
    `# ${page.title}`,
    `> ${page.summary}`,
    `Website: ${docsOrigin}${docPath(page)}\nDocumentation version: v${meta.latestVersion}`,
    ...page.sections.map((section) => [
      `## ${section.title}`,
      ...section.blocks.map(blockMarkdown),
    ].join("\n\n")),
    `## Source notes\n\n${page.sources.map((source) => `- [${source}](${meta.repositoryUrl}/blob/master/${source})`).join("\n")}`,
  ].join("\n\n") + "\n";
}

export function renderLlmsIndex(meta: ProjectMeta = defaultProjectMeta): string {
  return [
    "# kickstart",
    "> kickstart generates deterministic starter repos for humans and coding agents: services, frontends, libraries, CLIs, and systems.",
    `Documentation version: v${meta.latestVersion}. Start with the guides below; they link to clean Markdown.`,
    "Use system for aggregate repos; mono and monorepo are legacy aliases. Cloudflare Workers are not Docker containers. --knowledge controls external metadata, not baseline project docs. Inspect AGENTS.md and .kickstart/scaffold.json before extending generated code. Add --gh only when GitHub repository creation is requested.",
    ...docGroups.map((group) => `## ${group}\n\n${documentationPages.filter((page) => page.group === group)
      .map((page) => `- [${page.title}](${docsOrigin}${markdownPath(page)}): ${page.summary}`).join("\n")}`),
    `## Full documentation\n\n- [Complete documentation](${docsOrigin}/llms-full.txt): All public pages above in one text response, including commands, constraints, and source notes.`,
  ].join("\n\n") + "\n";
}

export function renderLlmsFull(meta: ProjectMeta = defaultProjectMeta): string {
  return [
    "# kickstart documentation",
    `> Complete public usage documentation for kickstart v${meta.latestVersion}. The human pages and this export share the same content source.`,
    `Index: ${docsOrigin}/llms.txt`,
    ...documentationPages.map((page) => `---\n\n${renderDocMarkdown(page, meta).trimEnd()}`),
  ].join("\n\n") + "\n";
}
