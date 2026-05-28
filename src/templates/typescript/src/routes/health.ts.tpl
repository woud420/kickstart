import type { Hono } from "hono";

export function registerHealthRoutes(app: Hono): void {
  app.get("/healthz", (c) =>
    c.json({
      status: "ok",
      service: "{{ service_name }}",
    }),
  );

  app.get("/readyz", (c) =>
    c.json({
      status: "ready",
      service: "{{ service_name }}",
    }),
  );
}
