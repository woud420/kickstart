import { describe, expect, it } from "vitest";

import worker from "../src/index";

const defaultEnv = {
  SERVICE_NAME: "kickstart-site",
};

describe("kickstart website worker", () => {
  it("returns health status", async () => {
    const request = new Request("https://example.test/healthz") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ok",
      service: "kickstart-site",
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
    expect(body).toContain("Contact: mailto:jm@polarcoordinates.org");
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
    expect(html).toContain("/assets/site.css?v=0.4.2");
    expect(html).toContain("/assets/site.js?v=0.4.2");
    expect(html).toContain("v0.4.2");
    expect(html).toContain("Trustworthy releases, leaner manifests, adopt preview");
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
    const request = new Request("https://example.test/assets/site.js?v=0.4.2") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);
    const script = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/javascript");
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(script).toContain("navigator.clipboard");
    expect(script).toContain('"output":"./Dockerfile\\n./Makefile');
    expect(script).not.toContain('"output":"./Dockerfile\\\\n./Makefile');
    expect(script).toContain("kickstart create system platform --cloud aws --runtime kubernetes --knowledge none");
    expect(script).toContain("docs/agents/recommended-agents.md");
    expect(script).not.toContain("docs/agents/recommended.md");
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
    expect(html).toContain("src/clients/cache.py");
    expect(html).toContain("Redis client");
    expect(html).toContain("services are explicit");
    expect(html).toContain("component map");
  });
});
