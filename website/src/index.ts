import { siteScript } from "./assets/site-script";
import { copyScript } from "./assets/copy-script";
import { siteStyles } from "./assets/site-styles";
import { docsStyles } from "./assets/docs-styles";
import { findDocPage } from "./docs/content";
import { renderDocHtml, renderDocNotFound } from "./docs/html";
import { docsOrigin, renderDocMarkdown, renderLlmsFull, renderLlmsIndex } from "./docs/markdown";
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
const WWW_HOSTNAME = `www.${PUBLIC_HOSTNAME}`;
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

function documentationText(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
      "link": `<${docsOrigin}/llms.txt>; rel="describedby"`,
    },
  });
}

function isPublicHostname(hostname: string): boolean {
  return hostname.toLowerCase() === PUBLIC_HOSTNAME;
}

function isWwwHostname(hostname: string): boolean {
  return hostname.toLowerCase() === WWW_HOSTNAME;
}

function httpsRedirect(url: URL): Response {
  const redirectUrl = new URL(url);
  redirectUrl.protocol = "https:";
  return Response.redirect(redirectUrl.toString(), 308);
}

function apexRedirect(url: URL): Response {
  const redirectUrl = new URL(url);
  redirectUrl.protocol = "https:";
  redirectUrl.hostname = PUBLIC_HOSTNAME;
  redirectUrl.port = "";
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

    // Before the HTTPS redirect so http://www reaches the HTTPS apex in one hop.
    if (isWwwHostname(url.hostname)) {
      return apexRedirect(url);
    }

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

    if (url.pathname === "/assets/docs.css") {
      return withSecurityHeaders(assetResponse(docsStyles, "text/css; charset=utf-8"), url);
    }

    if (url.pathname === "/assets/copy.js") {
      return withSecurityHeaders(assetResponse(copyScript, "application/javascript; charset=utf-8"), url);
    }

    if (url.pathname === "/llms.txt" || url.pathname === "/llms-full.txt") {
      const meta = resolveProjectMeta(env);
      const body = url.pathname === "/llms.txt" ? renderLlmsIndex(meta) : renderLlmsFull(meta);
      return withSecurityHeaders(documentationText(body), url);
    }

    if (url.pathname === "/docs" || url.pathname === "/docs/") {
      const destination = new URL(url);
      destination.pathname = "/docs/get-started";
      return withSecurityHeaders(Response.redirect(destination.toString(), 308), url);
    }

    if (url.pathname.startsWith("/docs/")) {
      const slug = url.pathname.slice("/docs/".length).replace(/\/$/, "");
      const isMarkdown = slug.endsWith(".md");
      const page = findDocPage(isMarkdown ? slug.slice(0, -3) : slug);
      if (page && url.pathname.endsWith("/")) {
        const destination = new URL(url);
        destination.pathname = `/docs/${slug}`;
        return withSecurityHeaders(Response.redirect(destination.toString(), 308), url);
      }
      const meta = resolveProjectMeta(env);
      if (isMarkdown) {
        return withSecurityHeaders(documentationText(
          page ? renderDocMarkdown(page, meta) : "Documentation page not found.\n", page ? 200 : 404,
        ), url);
      }
      return withSecurityHeaders(new Response(page ? renderDocHtml(page, meta) : renderDocNotFound(meta), {
        status: page ? 200 : 404,
        headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
      }), url);
    }

    return withSecurityHeaders(htmlResponse(resolveProjectMeta(env)), url);
  },
} satisfies ExportedHandler<Env>;
