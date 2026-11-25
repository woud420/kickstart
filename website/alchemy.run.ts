import * as Alchemy from "alchemy";
import * as Cloudflare from "alchemy/Cloudflare";
import { Stack } from "alchemy/Stack";
import { localState } from "alchemy/State";
import * as Effect from "effect/Effect";

import { resolveReleaseConfig } from "./scripts/render-release-config";

const config = resolveReleaseConfig(process.argv.slice(2), process.env);

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

// Deploying a site whose hero and release-notes links point at a
// nonexistent GitHub release publishes 404s (exactly the stranded-v0.4.3
// failure mode). Make "the release URL resolves" a deploy precondition
// instead of a timing coincidence. A Stack may only fail with config errors,
// so a missing release aborts the deploy as a defect.
const releaseUrlResolves = (releaseUrl: string) =>
  Effect.tryPromise(() => fetch(releaseUrl, { method: "HEAD", redirect: "follow" })).pipe(
    Effect.flatMap((response) =>
      response.ok
        ? Effect.void
        : Effect.fail(
            new Error(
              `release URL does not resolve (HTTP ${response.status}): ${releaseUrl} — ` +
                "publish the release (tag + release workflow) before deploying the website.",
            ),
          ),
    ),
    Effect.orDie,
  );

export default Alchemy.Stack(
  "kickstart-site",
  {
    providers: Cloudflare.providers(),
    // CI runners start empty, so state is a local file and every release
    // deploy adopts the existing Worker and custom domains by name
    // (`alchemy deploy --adopt`).
    state: localState(),
  },
  Effect.gen(function* () {
    const { stage } = yield* Stack;
    const isProd = stage === "prod";

    if (isProd) {
      yield* releaseUrlResolves(config.releaseUrl);
    }

    const worker = yield* Cloudflare.Worker("website", {
      name: workerNameForStage(config.serviceName, stage),
      main: "./src/index.ts",
      compatibility: { date: "2026-05-02" },
      workersDev: { enabled: true, previewsEnabled: false },
      // www is bound to the same Worker so Cloudflare creates its DNS record;
      // the Worker answers it with a permanent redirect to the apex.
      domain:
        isProd && config.domain !== ""
          ? { name: config.domain, aliases: [`www.${config.domain}`] }
          : undefined,
      env: {
        SERVICE_NAME: config.serviceName,
        PROJECT_VERSION: config.version,
        SUPPORTED_FROM_VERSION: config.supportedFrom,
        REPOSITORY_URL: config.repositoryUrl,
        RELEASE_URL: config.releaseUrl,
        DEPLOY_PROBE_SHA256: process.env.DEPLOY_PROBE_SHA256 ?? "",
        DEPLOY_PROBE_EXPIRES_AT: process.env.DEPLOY_PROBE_EXPIRES_AT ?? "",
      },
    });

    return { version: config.version, url: worker.url, urls: worker.urls };
  }),
);
