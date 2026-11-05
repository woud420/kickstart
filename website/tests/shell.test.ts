import { describe, expect, it } from "vitest";

import { copyScript } from "../src/assets/copy-script";
import worker from "../src/index";

function request(path: string) {
  return worker.fetch(new Request(`https://kickstart-cli.org${path}`) as Parameters<typeof worker.fetch>[0], {});
}

describe("shared website shell", () => {
  it("gives the landing page and docs the same fonts, favicon, and core styles", async () => {
    const home = await (await request("/")).text();
    const docs = await (await request("/docs/get-started")).text();
    const fontLink = /<link href="(https:\/\/fonts.googleapis.com[^\"]+)" rel="stylesheet"/.exec(home)?.[1];
    expect(fontLink).toContain("Fraunces");
    expect(fontLink).toContain("Atkinson+Hyperlegible");
    expect(fontLink).toContain("IBM+Plex+Mono");
    expect(docs).toContain(`href="${fontLink}"`);
    const favicon = /<link rel="icon" href="([^\"]+)"/.exec(home)?.[1];
    expect(favicon).toBeDefined();
    expect(docs).toContain(`rel="icon" href="${favicon}"`);
    for (const html of [home, docs]) {
      expect(html).toContain('/assets/site.css?v=');
      expect(html).toContain('aria-label="Main navigation"');
      expect(html).toContain('aria-label="kickstart home"');
      expect(html).toContain('href="#main">Skip to content</a>');
      expect(html).not.toContain("Geist");
    }
  });

  it("routes docs header links back to the landing page sections", async () => {
    const home = await (await request("/")).text();
    const docs = await (await request("/docs/get-started")).text();
    for (const anchor of ["examples", "positioning", "release"]) {
      expect(docs).toContain(`href="/#${anchor}"`);
      expect(home).toContain(`id="${anchor}"`);
    }
  });

  it("serves the shared copy behavior without loading example-tab code on docs", async () => {
    const docs = await (await request("/docs/get-started")).text();
    expect(docs).toContain('/assets/copy.js?v=');
    expect(docs).not.toContain('/assets/site.js?v=');
    const response = await request("/assets/copy.js");
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/javascript");
    expect(await response.text()).toContain("navigator.clipboard.writeText");
  });

  it.each([false, true])("copies the original command with clipboard failure=%s", async (blocked) => {
    let listener: (() => Promise<void>) | undefined;
    let copied = "";
    let selected = false;
    let reset: (() => void) | undefined;
    const attributes = new Map<string, string>();
    const button = {
      textContent: "copy",
      getAttribute: () => "example",
      setAttribute: (key: string, value: string) => attributes.set(key, value),
      removeAttribute: (key: string) => attributes.delete(key),
      addEventListener: (_event: string, callback: () => Promise<void>) => { listener = callback; },
    };
    const source = { textContent: "wrapped display", getAttribute: () => "original one-line command" };
    const status = { textContent: "" };
    new Function("document", "navigator", "window", copyScript)(
      { querySelector: () => status, querySelectorAll: () => [button], getElementById: () => source },
      { clipboard: { writeText: async (value: string) => { if (blocked) throw new Error("blocked"); copied = value; } } },
      { getSelection: () => ({ selectAllChildren: () => { selected = true; } }), clearTimeout: () => {}, setTimeout: (callback: () => void) => { reset = callback; return 1; } },
    );
    expect(listener).toBeDefined();
    await listener!();
    expect(button.textContent).toBe(blocked ? "selected" : "copied");
    expect(selected).toBe(blocked);
    if (blocked) expect(status.textContent).toContain("command is selected");
    else expect(copied).toBe("original one-line command");
    reset!();
    expect(button.textContent).toBe("copy");
    expect(attributes.has("data-state")).toBe(false);
  });
});
