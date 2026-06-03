import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { logger as honoLogger } from "hono/logger";
import { secureHeaders } from "hono/secure-headers";
import pino from "pino";

import { env } from "./config/env.js";
import { registerHealthRoutes } from "./routes/health.js";

export function buildApp(): Hono {
  const log = pino({ level: env.LOG_LEVEL });
  const app = new Hono();

  app.use("*", secureHeaders());
  app.use(
    "*",
    honoLogger((message) => log.info(message)),
  );

  registerHealthRoutes(app);

  return app;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const app = buildApp();
  serve({ fetch: app.fetch, hostname: env.HOST, port: env.PORT });
}
