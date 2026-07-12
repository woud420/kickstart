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

const PUBLIC_HOSTNAME = "kickstart-cli.org";
const HSTS_HEADER_VALUE = "max-age=15552000";
const SECURITY_TXT = `Contact: mailto:jim@polarcoordinates.org
Expires: 2027-06-26T00:00:00Z
Preferred-Languages: en
Canonical: https://${PUBLIC_HOSTNAME}/.well-known/security.txt
`;

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

function securityTextResponse(): Response {
  return new Response(SECURITY_TXT, {
    headers: {
      "cache-control": "public, max-age=3600",
      "content-type": "text/plain; charset=utf-8",
    },
  });
}

function isPublicHostname(hostname: string): boolean {
  return hostname.toLowerCase() === PUBLIC_HOSTNAME;
}

function httpsRedirect(url: URL): Response {
  const redirectUrl = new URL(url);
  redirectUrl.protocol = "https:";
  return Response.redirect(redirectUrl.toString(), 308);
}

function withSecurityHeaders(response: Response, url: URL): Response {
  if (url.protocol !== "https:" || !isPublicHostname(url.hostname)) {
    return response;
  }

  const headers = new Headers(response.headers);
  headers.set("strict-transport-security", HSTS_HEADER_VALUE);
  return new Response(response.body, {
    headers,
    status: response.status,
    statusText: response.statusText,
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

    if (url.protocol === "http:" && isPublicHostname(url.hostname)) {
      return httpsRedirect(url);
    }

    if (url.pathname === "/.well-known/security.txt") {
      return withSecurityHeaders(securityTextResponse(), url);
    }

    if (url.pathname === "/healthz") {
      // Version in the health payload makes deployed-vs-source drift
      // observable: the release pipeline asserts this equals the tag.
      const version = stripVersionPrefix(env.PROJECT_VERSION ?? defaultProjectMeta.latestVersion);
      return withSecurityHeaders(jsonResponse({ status: "ok", service, version }), url);
    }

    if (url.pathname === "/assets/site.css") {
      return withSecurityHeaders(
        assetResponse(siteStyles, "text/css; charset=utf-8"),
        url,
      );
    }

    if (url.pathname === "/assets/site.js") {
      return withSecurityHeaders(
        assetResponse(siteScript, "application/javascript; charset=utf-8"),
        url,
      );
    }

    return withSecurityHeaders(htmlResponse(resolveProjectMeta(env)), url);
  },
} satisfies ExportedHandler<Env>;
