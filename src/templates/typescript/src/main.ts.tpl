import Fastify from "fastify";
import helmet from "@fastify/helmet";

import { env } from "./config/env.js";
import { registerHealthRoutes } from "./routes/health.js";

export async function buildApp() {
  const app = Fastify({
    logger: {
      level: env.LOG_LEVEL,
    },
  });

  await app.register(helmet);
  await registerHealthRoutes(app);

  return app;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const app = await buildApp();
  await app.listen({ host: env.HOST, port: env.PORT });
}
