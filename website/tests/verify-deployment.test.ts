import { createHash } from "node:crypto";
import { describe, expect, it, vi } from "vitest";

import { prepareDeployProbe } from "../scripts/prepare-deploy-probe";
import { DEPLOY_PROBE_URL, verifyDeployment } from "../scripts/verify-deployment";
import worker from "../src/index";

const token = "b".repeat(64);
const healthy = { status: "ok", service: "kickstart-site", version: "0.4.6" };

describe("deployment verification", () => {
  it("creates independent tokens with a digest and a fifteen-minute lifetime", () => {
    const before = Date.now();
    const first = prepareDeployProbe();
    const second = prepareDeployProbe();
    expect(first.DEPLOY_PROBE_TOKEN).toMatch(/^[a-f0-9]{64}$/);
    expect(first.DEPLOY_PROBE_TOKEN).not.toBe(second.DEPLOY_PROBE_TOKEN);
    expect(first.DEPLOY_PROBE_SHA256).toBe(createHash("sha256").update(first.DEPLOY_PROBE_TOKEN).digest("hex"));
    expect(Number(first.DEPLOY_PROBE_EXPIRES_AT)).toBeGreaterThanOrEqual(before + 900_000);
    expect(Number(first.DEPLOY_PROBE_EXPIRES_AT)).toBeLessThanOrEqual(Date.now() + 900_000);
  });

  it("verifies the real Worker handler with the generated credential", async () => {
    const probe = prepareDeployProbe();
    const fetcher = vi.fn(async (input, init) => worker.fetch(
      new Request(input, init) as Parameters<typeof worker.fetch>[0], {
        ...probe, PROJECT_VERSION: "0.4.6", SERVICE_NAME: "kickstart-site",
      },
    )) as unknown as typeof fetch;
    await verifyDeployment({ token: probe.DEPLOY_PROBE_TOKEN, version: "0.4.6", fetcher, log: vi.fn() });
    expect(fetcher).toHaveBeenCalledOnce();
    expect(fetcher).toHaveBeenCalledWith(DEPLOY_PROBE_URL, expect.objectContaining({
      redirect: "error", signal: expect.any(AbortSignal),
      headers: { authorization: `Bearer ${probe.DEPLOY_PROBE_TOKEN}` },
    }));
  });

  it.each([
    () => new Response(null, { status: 403 }),
    () => new Response("not JSON"),
    () => Response.json({ ...healthy, version: "0.4.5" }),
    () => Response.json({ ...healthy, service: "another-worker" }),
    () => Response.json({ ...healthy, status: "error" }),
    () => Response.json(null),
    () => { throw new Error(`network error containing ${token}`); },
  ])("fails safely after bounded retries", async (response) => {
    const fetcher = vi.fn(async () => response()) as unknown as typeof fetch;
    const sleep = vi.fn(async () => {});
    const log = vi.fn();
    await expect(verifyDeployment({ token, version: "0.4.6", fetcher, sleep, log })).rejects.toThrow("five attempts");
    expect(fetcher).toHaveBeenCalledTimes(5);
    expect(sleep).toHaveBeenCalledTimes(4);
    expect(JSON.stringify(log.mock.calls)).not.toContain(token);
  });

  it("recovers when a stale deployment converges", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(Response.json({ ...healthy, version: "0.4.5" }))
      .mockResolvedValueOnce(Response.json(healthy)) as unknown as typeof fetch;
    const sleep = vi.fn(async () => {});
    await verifyDeployment({ token, version: "0.4.6", fetcher, sleep, log: vi.fn() });
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(sleep).toHaveBeenCalledOnce();
  });

  it.each([{ token: "", version: "0.4.6" }, { token, version: "0.4.6-rc.1" }])(
    "rejects incomplete input before making a request", async (options) => {
      const fetcher = vi.fn() as unknown as typeof fetch;
      await expect(verifyDeployment({ ...options, fetcher })).rejects.toThrow("required");
      expect(fetcher).not.toHaveBeenCalled();
    },
  );
});
