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
    expect(await response.text()).toContain("Starter repos for humans and agents");
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
    expect(html).toContain("https://github.com/example/kickstart");
    expect(html).toContain("https://github.com/example/kickstart/releases/tag/v0.5.0");
  });

  it("renders the first-screen example", async () => {
    const request = new Request("https://example.test/examples") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);

    const html = await response.text();

    expect(response.status).toBe(200);
    expect(html).toContain("Starter repos for humans and agents");
    expect(html).toContain("Generate an API service with clients");
    expect(html).toContain("component map");
  });

  it("states what Kickstart is and is not", async () => {
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
    expect(await response.text()).toContain(".hero");
  });

  it("serves script assets", async () => {
    const request = new Request("https://example.test/assets/site.js") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(request, defaultEnv);
    const script = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("application/javascript");
    expect(script).toContain("navigator.clipboard");
    expect(script).toContain('"output":"./Dockerfile\\n./Makefile');
    expect(script).not.toContain('"output":"./Dockerfile\\\\n./Makefile');
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
