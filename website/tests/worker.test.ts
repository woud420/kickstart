import { describe, expect, it } from "vitest";

import worker from "../src/index";
import { commandExamples, defaultProjectMeta, installCommand, releaseNotes } from "../src/site/content";

const defaultEnv = {
  SERVICE_NAME: "kickstart-site",
};

// The current version comes from content.ts (itself test-pinned to
// pyproject.toml), so a release bump updates these assertions for free
// instead of requiring four hand-edited version strings.
const latestVersion = defaultProjectMeta.latestVersion;

describe("kickstart website worker", () => {
  it("returns health status with the served version", async () => {
    const request = new Request("https://example.test/healthz") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ok",
      service: "kickstart-site",
      version: latestVersion,
    });
  });

  it("reports the deployed version from Worker vars in /healthz", async () => {
    const request = new Request("https://example.test/healthz") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, { ...defaultEnv, PROJECT_VERSION: "v9.9.9" });

    expect(await response.json()).toEqual({
      status: "ok",
      service: "kickstart-site",
      version: "9.9.9",
    });
  });

  it("redirects the production hostname from HTTP to HTTPS", async () => {
    const request = new Request("http://kickstart-cli.org/generate") as Parameters<
      typeof worker.fetch
    >[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe(
      "https://kickstart-cli.org/generate",
    );
  });

  it("adds HSTS on the production hostname", async () => {
    const request = new Request("https://kickstart-cli.org/") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.headers.get("strict-transport-security")).toBe(
      "max-age=15552000",
    );
  });

  it("serves security.txt", async () => {
    const request = new Request("https://kickstart-cli.org/.well-known/security.txt") as Parameters<
      typeof worker.fetch
    >[0];

    const response = await worker.fetch(request, defaultEnv);
    const body = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/plain");
    expect(body).toContain("Contact: mailto:jim@polarcoordinates.org");
    expect(body).toContain("Canonical: https://kickstart-cli.org/.well-known/security.txt");
  });

  it("serves the SPA shell", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    expect(response.headers.get("cache-control")).toBe("no-store");
    const html = await response.text();
    expect(html).toContain('<h1 id="hero-title">kickstart</h1>');
    expect(html).toContain(`/assets/site.css?v=${latestVersion}`);
    expect(html).toContain(`/assets/site.js?v=${latestVersion}`);
    expect(html).toContain(`v${latestVersion}`);
    expect(html).toContain("Sandbox bootstrap, tiered eval runner, coverage and badges");
    expect(html).toContain("Scaffold contract convergence");
  });

  it("renders version and repository metadata from Worker vars", async () => {
    const request = new Request("https://example.test/release") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, {
      PROJECT_VERSION: "v0.5.0",
      RELEASE_URL: "https://github.com/example/kickstart/releases/tag/v0.5.0",
      REPOSITORY_URL: "https://github.com/example/kickstart",
      SERVICE_NAME: "kickstart-site",
    });

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("v0.5.0");
    expect(html).toContain("/assets/site.css?v=0.5.0");
    expect(html).toContain("/assets/site.js?v=0.5.0");
    expect(html).toContain("https://github.com/example/kickstart");
    expect(html).toContain("https://github.com/example/kickstart/releases/tag/v0.5.0");
  });

  it("renders the first-screen example", async () => {
    const request = new Request("https://example.test/examples") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("Starter repos for humans and agents");
    expect(html).toContain("python service");
    expect(html).toContain("component map");
  });

  it("states what kickstart is and is not", async () => {
    const request = new Request("https://example.test/positioning") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("Useful setup. Not architecture");
    expect(html).toContain("Scaffold factory");
    expect(html).toContain("Product architect");
  });

  it("serves stylesheet assets", async () => {
    const request = new Request("https://example.test/assets/site.css") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/css");
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.text()).toContain(".hero");
  });

  it("serves script assets", async () => {
    const request = new Request(`https://example.test/assets/site.js?v=${latestVersion}`) as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);
    const script = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/javascript");
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(script).toContain("navigator.clipboard");
    expect(script).toContain('"outputHtml":"api/\\n├── Dockerfile\\n├── Makefile');
    expect(script).not.toContain('"outputHtml":"api/\\\\n├── Dockerfile');
    expect(script).toContain('├── <span class=\\"agent-path\\">AGENTS.md</span>');
    expect(script).toContain("kickstart create system platform --cloud aws --runtime kubernetes --knowledge none");
    expect(script).toContain('└── docs/ <span class=\\"tree-count\\">(5 files)</span>');
    expect(script).not.toContain("agents/recommended.md");
    expect(script).toContain("tools/");
    expect(script).not.toContain("config/tsconfig/base.json");
    expect(script).not.toContain("tsconfig.base.json");
    expect(script).not.toContain("kickstart create system platform --cloud cloudflare --runtime cloudflare-workers");
  });

  it("falls back to the SPA for client-side routes", async () => {
    const request = new Request("https://example.test/generate") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(await response.text()).toContain("kickstart create service api");
  });

  it("shows concrete generated files and component details", async () => {
    const request = new Request("https://example.test/generate") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain('├── src/ <span class="tree-count">(7 files)</span>');
    expect(html).toContain("src/clients/cache.py");
    expect(html).toContain("Redis client");
    expect(html).toContain("services are explicit");
    expect(html).toContain("component map");
  });

  it("marks the agent contract in the tree and the component map", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const html = await (await worker.fetch(request, defaultEnv)).text();

    expect(html).toContain('├── <span class="agent-path">.kickstart/scaffold.json</span>');
    expect(html).toContain('├── <span class="agent-path">CLAUDE.md</span>');
    expect(html).toContain('<li class="component-node is-agent">');
    expect(html).toContain("agent contract");
  });

  it("leads with a copyable install command", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const html = await (await worker.fetch(request, defaultEnv)).text();

    expect(html).toContain(`<code id="install-command" data-copy="${installCommand}">`);
    expect(html).toContain('data-copy-target="install-command"');
    expect(html).toContain('id="install"');
  });

  it("wires the example tabs to one labelled tab panel", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const html = await (await worker.fetch(request, defaultEnv)).text();

    expect(html.match(/role="tab"/g)).toHaveLength(commandExamples.length);
    expect(html.match(/aria-controls="example-panel"/g)).toHaveLength(commandExamples.length);
    expect(html).toContain('id="example-panel" role="tabpanel" aria-labelledby="tab-service"');
    expect(html.match(/tabindex="0"/g)).toHaveLength(1);
    expect(html.match(/<ul class="component-flow[^"]*" data-example=/g)).toHaveLength(commandExamples.length);
    expect(html.match(/component-flow is-active/g)).toHaveLength(1);
  });

  it("opens only the newest release note", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const html = await (await worker.fetch(request, defaultEnv)).text();

    expect(html.match(/<details class="release-note"/g)).toHaveLength(releaseNotes.length);
    expect(html.match(/<details class="release-note" open>/g)).toHaveLength(1);
    expect(html.indexOf("<details class=\"release-note\" open>")).toBeLessThan(html.indexOf(`v${releaseNotes[1]?.version}`));
  });
});
