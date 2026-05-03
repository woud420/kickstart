interface Env {
  SERVICE_NAME?: string;
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const service = env.SERVICE_NAME ?? "hello-worker";

    if (url.pathname === "/healthz") {
      return jsonResponse({ status: "ok", service });
    }

    return jsonResponse({ message: "Hello from " + service });
  },
} satisfies ExportedHandler<Env>;
