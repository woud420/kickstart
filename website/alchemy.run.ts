import alchemy from "alchemy";
import type { Scope } from "alchemy";
import { Worker, Zone } from "alchemy/cloudflare";
import { CloudflareStateStore } from "alchemy/state";

import { resolveReleaseConfig } from "./scripts/render-release-config";

const config = resolveReleaseConfig(Bun.argv.slice(2), process.env);

function alchemyStateStore() {
  const hasPassword = Boolean(process.env.ALCHEMY_PASSWORD);
  const hasStateToken = Boolean(process.env.ALCHEMY_STATE_TOKEN);

  if (hasPassword !== hasStateToken) {
    throw new Error(
      "Persistent state is half-configured: set both ALCHEMY_PASSWORD and ALCHEMY_STATE_TOKEN " +
        "(or neither, to deploy with ephemeral state). Refusing to silently fall back.",
    );
  }

  if (!hasPassword) {
    return undefined;
  }

  return (scope: Scope) => new CloudflareStateStore(scope);
}

function workerNameForStage(serviceName: string, stage: string): string {
  if (stage === "prod") {
    return serviceName;
  }

  const suffix = stage
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return `${serviceName}-${suffix || "dev"}`;
}

const app = await alchemy("kickstart-site", {
  stateStore: alchemyStateStore(),
});

const workerName = workerNameForStage(config.serviceName, app.stage);
const workerDomains =
  app.stage === "prod" && config.domain !== ""
    ? [{ domainName: config.domain, adopt: true }]
    : undefined;

if (app.stage === "prod" && config.domain !== "") {
  await Zone("zone-security", {
    name: config.domain,
    type: "full",
    settings: {
      ssl: "strict",
      alwaysUseHttps: "on",
      automaticHttpsRewrites: "on",
    },
    botManagement: {
      fightMode: true,
      aiBotsProtection: "block",
      crawlerProtection: "enabled",
    },
  });
}

// Deploying a site whose hero and release-notes links point at a
// nonexistent GitHub release publishes 404s (exactly the stranded-v0.4.3
// failure mode). Make "the release URL resolves" a deploy precondition
// instead of a timing coincidence.
if (app.stage === "prod") {
  const releaseCheck = await fetch(config.releaseUrl, { method: "HEAD", redirect: "follow" });
  if (!releaseCheck.ok) {
    throw new Error(
      `release URL does not resolve (HTTP ${releaseCheck.status}): ${config.releaseUrl} — ` +
        "publish the release (tag + release workflow) before deploying the website.",
    );
  }
}

export const worker = await Worker("website", {
  name: workerName,
  entrypoint: "./src/index.ts",
  compatibilityDate: "2026-05-02",
  adopt: true,
  url: true,
  domains: workerDomains,
  bindings: {
    SERVICE_NAME: config.serviceName,
    PROJECT_VERSION: config.version,
    SUPPORTED_FROM_VERSION: config.supportedFrom,
    REPOSITORY_URL: config.repositoryUrl,
    RELEASE_URL: config.releaseUrl,
  },
});

console.log(`Configured ${workerName} for v${config.version}`);
if (workerDomains !== undefined) {
  console.log(`Configured custom domain ${config.domain}`);
}

await app.finalize();
