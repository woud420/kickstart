import { describe, expect, it } from "vitest";

import worker from "../src/index";

const defaultEnv = {
  SERVICE_NAME: "kickstart-site",
};

describe("Kickstart website worker", () => {
  it("returns health status", async () => {
    const request = new Request("https://example.test/healthz") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ok",
      service: "kickstart-site",
    });
  });

  it("serves the SPA shell", async () => {
    const request = new Request("https://example.test/") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    expect(await response.text()).toContain("Reviewable starter repos");
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
    expect(html).toContain("Release v0.5.0");
    expect(html).toContain("https://github.com/example/kickstart");
    expect(html).toContain("https://github.com/example/kickstart/releases/tag/v0.5.0");
  });

  it("renders the scaffold contract", async () => {
    const request = new Request("https://example.test/contract") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("Kickstart encodes the project shape once");
    expect(html).toContain("Docker, Cloudflare Workers, Kubernetes where relevant");
    expect(html).toContain("tests, typecheck, docs, CI, release artifacts");
  });

  it("states what Kickstart is and is not", async () => {
    const request = new Request("https://example.test/positioning") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("A scaffold contract, not a software generator");
    expect(html).toContain("Opinionated scaffold factory");
    expect(html).toContain("Product architect");
  });

  it("serves stylesheet assets", async () => {
    const request = new Request("https://example.test/assets/site.css") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/css");
    expect(await response.text()).toContain(".hero");
  });

  it("serves script assets", async () => {
    const request = new Request("https://example.test/assets/site.js") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/javascript");
    expect(await response.text()).toContain("navigator.clipboard");
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
    expect(html).toContain("dependency containers are not generated yet");
    expect(html).toContain("component map");
  });
});
