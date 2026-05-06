import alchemy from "alchemy";
import type { Scope } from "alchemy";
import { Worker } from "alchemy/cloudflare";
import { CloudflareStateStore } from "alchemy/state";

import { resolveReleaseConfig } from "./scripts/render-release-config";

const config = resolveReleaseConfig(Bun.argv.slice(2), process.env);

function alchemyStateStore() {
  if (!process.env.ALCHEMY_PASSWORD || !process.env.ALCHEMY_STATE_TOKEN) {
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

export const worker = await Worker("website", {
  name: workerName,
  entrypoint: "./src/index.ts",
  compatibilityDate: "2026-05-02",
  adopt: true,
  url: true,
  bindings: {
    SERVICE_NAME: config.serviceName,
    PROJECT_VERSION: config.version,
    SUPPORTED_FROM_VERSION: config.supportedFrom,
    REPOSITORY_URL: config.repositoryUrl,
    RELEASE_URL: config.releaseUrl,
  },
});

console.log(`Configured ${workerName} for v${config.version}`);

await app.finalize();
