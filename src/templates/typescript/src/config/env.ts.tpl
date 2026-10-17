import { z } from "zod";

const envSchema = z.object({
  HOST: z.string().default("0.0.0.0"),
  PORT: z.coerce.number().int().positive().default(8080),
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
{% if database == "postgres" %}
  DATABASE_URL: z.string().url().default("postgres://postgres:postgres@127.0.0.1:5432/postgres"),
{% endif %}
});

export const env = envSchema.parse(process.env);
{% if auth == "jwt" %}

const jwtEnvSchema = z.object({
  JWT_SECRET: z.string().refine((secret) => secret.trim().length >= 32, {
    message: "JWT_SECRET must contain at least 32 non-padding characters",
  }),
  JWT_ALGORITHM: z.literal("HS256").default("HS256"),
  JWT_ISSUER: z.string().trim().min(1).default("{{ service_name }}"),
  JWT_ACCESS_TOKEN_SECONDS: z.coerce.number().int().positive().default(1800),
});

export type JwtConfig = z.infer<typeof jwtEnvSchema>;

// Validate when auth is configured so public health checks need no signing key.
export function loadJwtConfig(environment: NodeJS.ProcessEnv = process.env): JwtConfig {
  return jwtEnvSchema.parse(environment);
}
{% endif %}
