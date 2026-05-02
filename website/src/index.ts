import { siteScript } from "./assets/site-script";
import { siteStyles } from "./assets/site-styles";
import { defaultProjectMeta, type ProjectMeta } from "./site/content";
import { renderSiteHtml } from "./site/html";

interface Env {
  SERVICE_NAME?: string;
  PROJECT_VERSION?: string;
  SUPPORTED_FROM_VERSION?: string;
  REPOSITORY_URL?: string;
  RELEASE_URL?: string;
}

function jsonResponse(body: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...init?.headers,
    },
  });
}

function assetResponse(body: string, contentType: string): Response {
  return new Response(body, {
    headers: {
      "cache-control": "no-store",
      "content-type": contentType,
    },
  });
}

function stripVersionPrefix(version: string): string {
  return version.startsWith("v") ? version.slice(1) : version;
}

function resolveProjectMeta(env: Env): ProjectMeta {
  const latestVersion = stripVersionPrefix(env.PROJECT_VERSION ?? defaultProjectMeta.latestVersion);
  const supportedFrom = stripVersionPrefix(env.SUPPORTED_FROM_VERSION ?? defaultProjectMeta.supportedFrom);
  const repositoryUrl = env.REPOSITORY_URL ?? defaultProjectMeta.repositoryUrl;

  return {
    latestVersion,
    supportedFrom,
    repositoryUrl,
    releaseUrl: env.RELEASE_URL ?? `${repositoryUrl}/releases/tag/v${latestVersion}`,
  };
}

function htmlResponse(meta: ProjectMeta): Response {
  return new Response(renderSiteHtml(meta), {
    headers: {
      "cache-control": "no-store",
      "content-type": "text/html; charset=utf-8",
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const service = env.SERVICE_NAME ?? "kickstart-site";

    if (url.pathname === "/healthz") {
      return jsonResponse({ status: "ok", service });
    }

    if (url.pathname === "/assets/site.css") {
      return assetResponse(siteStyles, "text/css; charset=utf-8");
    }

    if (url.pathname === "/assets/site.js") {
      return assetResponse(siteScript, "application/javascript; charset=utf-8");
    }

    return htmlResponse(resolveProjectMeta(env));
  },
} satisfies ExportedHandler<Env>;
