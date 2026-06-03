import { describe, expect, it } from "vitest";

import { buildApp } from "../src/main.js";

describe("health routes", () => {
  it("returns health status", async () => {
    const app = buildApp();
    const response = await app.request("/healthz");

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ok",
      service: "{{ service_name }}",
    });
  });

  it("returns readiness status", async () => {
    const app = buildApp();
    const response = await app.request("/readyz");

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ready",
      service: "{{ service_name }}",
    });
  });
});
