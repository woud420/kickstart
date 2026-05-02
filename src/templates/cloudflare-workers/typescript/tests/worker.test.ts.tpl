import { describe, expect, it } from "vitest";

import worker from "../src/index";

describe("Cloudflare Worker", () => {
  it("returns health status", async () => {
    const request = new Request("https://example.test/healthz") as Parameters<typeof worker.fetch>[0];

    const response = await worker.fetch(
      request,
      { SERVICE_NAME: "{{ service_name }}" },
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "ok",
      service: "{{ service_name }}",
    });
  });
});
