import { z } from "zod";

const envSchema = z.object({
  HOST: z.string().default("0.0.0.0"),
  PORT: z.coerce.number().int().positive().default(8080),
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
{% if database == "postgres" %}
  DATABASE_URL: z.string().url().default("postgres://postgres:postgres@127.0.0.1:5432/postgres"),
{% endif %}
{% if cache == "redis" %}
  REDIS_URL: z.string().url().default("redis://127.0.0.1:6379/0"),
{% endif %}
});

export const env = envSchema.parse(process.env);
