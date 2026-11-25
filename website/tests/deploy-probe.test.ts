import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";

import worker from "../src/index";

const token = "a".repeat(64);
const env = {
  SERVICE_NAME: "kickstart-site",
  PROJECT_VERSION: "0.4.6",
  DEPLOY_PROBE_SHA256: createHash("sha256").update(token).digest("hex"),
  DEPLOY_PROBE_EXPIRES_AT: String(Date.now() + 60_000),
};

async function request(path: string, options: RequestInit = {}, bindings = env) {
  return worker.fetch(
    new Request(`https://kickstart-site.polarcoordinates.workers.dev${path}`, options) as Parameters<typeof worker.fetch>[0],
    bindings,
  );
}

describe("workers.dev deployment access", () => {
  it.each(["/", "/generate", "/assets/site.js", "/assets/site.css", "/.well-known/security.txt"])(
    "never serves %s, even with the deployment token", async (path) => {
      const response = await request(path, { headers: { authorization: `Bearer ${token}` } });
      expect(response.status).toBe(404);
      expect(await response.text()).not.toContain("kickstart");
    },
  );

  it.each([undefined, "Bearer wrong", `Basic ${token}`])("rejects invalid authentication %s", async (authorization) => {
    const response = await request("/healthz", { headers: authorization ? { authorization } : {} });
    expect(response.status).toBe(404);
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  it("returns only health metadata for an authorized deployment", async () => {
    const response = await request("/healthz", { headers: { authorization: `Bearer ${token}` } });
    expect(response.status).toBe(200);
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(await response.json()).toEqual({ status: "ok", service: "kickstart-site", version: "0.4.6" });
  });

  it.each(["0", "invalid", "", String(Date.now() - 1)])("rejects expired or invalid expiry %s", async (expiry) => {
    const response = await request("/healthz", { headers: { authorization: `Bearer ${token}` } }, {
      ...env, DEPLOY_PROBE_EXPIRES_AT: expiry,
    });
    expect(response.status).toBe(404);
  });

  it("fails closed without deployment configuration", async () => {
    const response = await request("/healthz", { headers: { authorization: `Bearer ${token}` } }, {
      ...env, DEPLOY_PROBE_SHA256: "", DEPLOY_PROBE_EXPIRES_AT: "",
    });
    expect(response.status).toBe(404);
  });

  it.each(["POST", "HEAD", "OPTIONS"])("rejects %s probes", async (method) => {
    expect((await request("/healthz", { method, headers: { authorization: `Bearer ${token}` } })).status).toBe(404);
  });

  it.each([
    "old-kickstart-site.polarcoordinates.workers.dev",
    "kickstart-site.polarcoordinates.workers.dev.",
  ])("protects provider hostname %s too", async (hostname) => {
    const response = await worker.fetch(
      new Request(`https://${hostname}/`) as Parameters<typeof worker.fetch>[0], env,
    );
    expect(response.status).toBe(404);
  });

  it("keeps the public custom domain accessible without a token", async () => {
    const response = await worker.fetch(
      new Request("https://kickstart-cli.org/") as Parameters<typeof worker.fetch>[0], env,
    );
    expect(response.status).toBe(200);
    expect(await response.text()).toContain("kickstart");
  });
});
