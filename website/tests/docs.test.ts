import { existsSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { docPath, documentationPages } from "../src/docs/content";
import { renderDocHtml } from "../src/docs/html";
import worker from "../src/index";

function request(path: string) {
  return worker.fetch(new Request(`https://kickstart-cli.org${path}`) as Parameters<typeof worker.fetch>[0], {});
}

describe("documentation", () => {
  it.each(["/docs", "/docs/"])("redirects %s to the first page and retains the query", async (path) => {
    const response = await request(`${path}?from=home`);
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe("https://kickstart-cli.org/docs/get-started?from=home");
  });

  for (const page of documentationPages) {
    it(`serves a complete deep link for ${page.slug}`, async () => {
      const response = await request(docPath(page));
      const html = await response.text();
      expect(response.status).toBe(200);
      expect(response.headers.get("content-type")).toBe("text/html; charset=utf-8");
      expect(response.headers.get("strict-transport-security")).toBe("max-age=15552000");
      expect(html).toContain(`<h1>${page.title}</h1>`);
      expect(html).toContain(`href="${docPath(page)}" aria-current="page"`);
      expect(html).toContain('<details class="docs-menu">');
      expect(html).toContain('aria-label="On this page"');
      expect(html).toContain('aria-live="polite"');
      expect(html).not.toContain('id="hero-title"');
      for (const section of page.sections) {
        expect(html).toContain(`id="${section.id}"`);
        expect(html).toContain(`href="#${section.id}"`);
      }
      for (const [, id] of html.matchAll(/data-copy-target="([^"]+)"/g)) {
        expect(html).toContain(`id="${id}"`);
      }
    });
  }

  it("keeps every docs link and anchor navigable", async () => {
    for (const page of documentationPages) {
      const html = await (await request(docPath(page))).text();
      for (const [, href = ""] of html.matchAll(/href="([^"]+)"/g)) {
        if (href.startsWith("#")) {
          expect(html, `${page.slug}: ${href}`).toContain(`id="${href.slice(1)}"`);
        } else if (href.startsWith("/docs/")) {
          expect((await request(href)).status, `${page.slug}: ${href}`).toBe(200);
        }
      }
    }
  });

  it("links source notes to real repository documents and code", () => {
    expect(new Set(documentationPages.map((page) => page.slug)).size).toBe(documentationPages.length);
    for (const page of documentationPages) {
      expect(page.sources.length).toBeGreaterThan(0);
      for (const source of page.sources) expect(existsSync(resolve("..", source)), source).toBe(true);
      expect(new Set(page.sections.map((section) => section.id)).size).toBe(page.sections.length);
    }
  });

  it("returns a real docs 404 without changing the landing-page fallback", async () => {
    for (const path of ["/docs/missing", "/docs/get-started/extra", "/docs/%3Cscript%3E"]) {
      const response = await request(path);
      expect(response.status).toBe(404);
      expect(await response.text()).toContain("Page not found");
    }
    expect(await (await request("/generate")).text()).toContain('id="hero-title"');
  });

  it("canonicalizes a trailing slash on a known page", async () => {
    const response = await request("/docs/get-started/?ref=example");
    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe("https://kickstart-cli.org/docs/get-started?ref=example");
  });

  it("serves docs styles and makes the docs discoverable from home", async () => {
    const response = await request("/assets/docs.css");
    expect(response.headers.get("content-type")).toContain("text/css");
    expect(await response.text()).toContain(".docs-menu");
    expect(await (await request("/")).text()).toContain('href="/docs/get-started">docs</a>');
  });

  it("escapes content in the document title, body, and copy attributes", () => {
    const html = renderDocHtml({
      slug: "escape-test", title: '<script>alert("title")</script>', group: "Guides", summary: '"<unsafe>', sources: [],
      sections: [{ id: "example", title: "A & B", blocks: [
        { kind: "paragraph", text: '<img src=x onerror="alert(1)"> `a < b`' },
        { kind: "code", label: 'A "quote"', value: 'echo "<unsafe>"', language: "bash" },
      ] }],
    });
    expect(html).not.toContain('<script>alert("title")</script>');
    expect(html).not.toContain("<img src=x");
    expect(html).toContain("&lt;script&gt;");
    expect(html).toContain("<code>a &lt; b</code>");
    expect(html).toContain('data-copy="echo &quot;&lt;unsafe&gt;&quot;"');
  });
});
