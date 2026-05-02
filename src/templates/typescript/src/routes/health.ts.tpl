import type { FastifyInstance } from "fastify";

export async function registerHealthRoutes(app: FastifyInstance) {
  app.get("/healthz", async () => ({
    status: "ok",
    service: "{{ service_name }}",
  }));

  app.get("/readyz", async () => ({
    status: "ready",
    service: "{{ service_name }}",
  }));
}
