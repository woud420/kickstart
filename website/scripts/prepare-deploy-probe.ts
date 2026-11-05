import { createHash, randomBytes } from "node:crypto";
import { appendFileSync } from "node:fs";

export function prepareDeployProbe() {
  const token = randomBytes(32).toString("hex");
  return {
    DEPLOY_PROBE_TOKEN: token,
    DEPLOY_PROBE_SHA256: createHash("sha256").update(token).digest("hex"),
    DEPLOY_PROBE_EXPIRES_AT: String(Date.now() + 15 * 60_000),
  };
}

if (import.meta.main) {
  const destination = process.env.GITHUB_ENV;
  if (!destination) throw new Error("GITHUB_ENV is required");
  const probe = prepareDeployProbe();
  console.log(`::add-mask::${probe.DEPLOY_PROBE_TOKEN}`);
  appendFileSync(destination, Object.entries(probe).map(([key, value]) => `${key}=${value}\n`).join(""));
}
