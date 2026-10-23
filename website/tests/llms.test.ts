import { describe, expect, it } from "vitest";

import { documentationPages, type DocPage } from "../src/docs/content";
import { renderDocMarkdown, renderLlmsFull } from "../src/docs/markdown";
import worker from "../src/index";
import { escapeHtml } from "../src/site/format";

function request(path: string, env: Parameters<typeof worker.fetch>[1] = {}) {
  return worker.fetch(new Request(`https://kickstart-cli.org${path}`) as Parameters<typeof worker.fetch>[0], env);
}

describe("agent documentation", () => {
  it.each(["/llms.txt", "/llms-full.txt"])("serves %s as discoverable UTF-8 text", async (path) => {
    const response = await request(path);
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toBe("text/plain; charset=utf-8");
    expect(response.headers.get("strict-transport-security")).toBe("max-age=15552000");
    expect(response.headers.get("link")).toContain('<https://kickstart-cli.org/llms.txt>');
    expect(response.headers.get("link")).toContain('rel="describedby"');
    const body = await response.text();
    expect(body.startsWith("# kickstart")).toBe(true);
    expect(body).not.toMatch(/<!doctype|<html|<script|docs-sidebar/i);
    expect(body.endsWith("\n")).toBe(true);
  });

  it("keeps the index concise and points every page to a working text resource", async () => {
    const body = await (await request("/llms.txt")).text();
    expect(body).toContain("## Get started\n");
    expect(body).toContain("## Guides\n");
    expect(body).toContain("## Reference\n");
    expect(body).not.toContain("```bash");
    const urls = [...body.matchAll(/\]\((https:\/\/kickstart-cli\.org[^)]+)\)/g)].map((match) => match[1]!);
    expect(urls).toHaveLength(documentationPages.length + 1);
    for (const url of urls) {
      const response = await request(new URL(url).pathname);
      expect(response.status, url).toBe(200);
      expect(response.headers.get("content-type"), url).toContain("text/plain");
    }
  });

  for (const page of documentationPages) {
    it(`exports the same content as the human page for ${page.slug}`, async () => {
      const textResponse = await request(`/docs/${page.slug}.md`);
      const markdown = await textResponse.text();
      const html = await (await request(`/docs/${page.slug}`)).text();
      const full = await (await request("/llms-full.txt")).text();
      expect(textResponse.status).toBe(200);
      expect(textResponse.headers.get("content-type")).toBe("text/plain; charset=utf-8");
      expect(full).toContain(markdown.trimEnd());
      expect(markdown).toContain(`# ${page.title}\n`);
      expect(html).toContain(`href="https://kickstart-cli.org/docs/${page.slug}.md"`);
      for (const section of page.sections) {
        expect(markdown).toContain(`## ${section.title}\n`);
        for (const block of section.blocks) {
          if (block.kind === "code") {
            expect(markdown).toContain(block.value);
            expect(html).toContain(`data-copy="${escapeHtml(block.value)}"`);
          } else if (block.kind === "paragraph" || block.kind === "note") {
            expect(markdown).toContain(block.text);
          }
        }
      }
    });
  }

  it("returns a text 404 for a missing Markdown resource", async () => {
    const response = await request("/docs/missing.md");
    expect(response.status).toBe(404);
    expect(response.headers.get("content-type")).toContain("text/plain");
    expect(await response.text()).toBe("Documentation page not found.\n");
  });

  it("canonicalizes a Markdown trailing slash", async () => {
    const response = await request("/docs/get-started.md/?ref=agent");
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe("https://kickstart-cli.org/docs/get-started.md?ref=agent");
  });

  it("uses the same configured release metadata for index, full export, and pages", async () => {
    for (const path of ["/llms.txt", "/llms-full.txt", "/docs/get-started.md"]) {
      const body = await (await request(path, { PROJECT_VERSION: "v9.8.7", REPOSITORY_URL: "https://github.com/example/kickstart" })).text();
      expect(body).toContain("v9.8.7");
      expect(body).not.toContain("v0.4.6");
      if (path !== "/llms.txt") expect(body).toContain("https://github.com/example/kickstart/blob/master/README.md");
    }
  });

  it("keeps special table cells and nested code fences valid Markdown", () => {
    const page: DocPage = {
      slug: "format-test", title: "Formatting", summary: "A formatting fixture.", group: "Reference", sources: [],
      sections: [{ id: "example", title: "Example", blocks: [
        { kind: "table", headers: ["Value"], rows: [["a | b\nc"]] },
        { kind: "code", label: "Nested fence", value: "```bash\necho hello\n```", language: "text" },
        { kind: "links", items: [{ title: "Runtimes", href: "/docs/project-types#runtimes", description: "Supported runtime boundaries." }] },
      ] }],
    };
    const markdown = renderDocMarkdown(page);
    expect(markdown).toContain("| a \\| b c |");
    expect(markdown).toContain("````text\n```bash\necho hello\n```\n````");
    expect(markdown).toContain("https://kickstart-cli.org/docs/project-types.md#runtimes");
  });

  it("does not expose local build or tracker metadata", () => {
    expect(renderLlmsFull()).not.toMatch(/ENG-\d+|\/Users\/|\/private\/tmp\/|\/\.git\//);
  });

  it("provides enough text to answer representative agent tasks", async () => {
    const index = await (await request("/llms.txt")).text();
    expect(index).toContain("https://kickstart-cli.org/docs/get-started.md");
    expect(index).toContain("https://kickstart-cli.org/docs/existing-repositories.md");
    const start = await (await request("/docs/get-started.md")).text();
    expect(start).toContain("kickstart create service hello --lang typescript --runtime cloudflare-workers");
    expect(start).toContain("cd hello\nmake check\nmake dev");
    const existing = await (await request("/docs/existing-repositories.md")).text();
    expect(existing).toContain("kickstart adopt path/to/repo --check");
    expect(existing).toContain("adopt --check is read-only");
    expect(existing).toContain("This command writes a file, unlike the inspection commands above");
    const full = await (await request("/llms-full.txt")).text();
    expect(full).toContain(start.trimEnd());
    expect(full).toContain(existing.trimEnd());
  });
});
