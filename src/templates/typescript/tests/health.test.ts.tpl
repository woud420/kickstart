import { describe, expect, it } from "vitest";

import { buildApp } from "../src/main.js";

describe("health routes", () => {
  it("returns health status", async () => {
    const app = await buildApp();
    const response = await app.inject({ method: "GET", url: "/healthz" });

    expect(response.statusCode).toBe(200);
    expect(response.json()).toEqual({
      status: "ok",
      service: "{{ service_name }}",
    });
  });
});
