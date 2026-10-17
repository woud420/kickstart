import { afterEach, describe, expect, it, vi } from "vitest";

import { loadJwtConfig } from "../src/config/env.js";
import { createJwtAuth } from "../src/handler/auth.js";

const TEST_SECRET = "test-only-jwt-secret-with-at-least-32-characters";

afterEach(() => vi.unstubAllEnvs());

describe("JWT configuration", () => {
  it("loads explicit defaults without a generated signing key", () => {
    expect(loadJwtConfig({ JWT_SECRET: TEST_SECRET })).toEqual({
      JWT_SECRET: TEST_SECRET,
      JWT_ALGORITHM: "HS256",
      JWT_ISSUER: "{{ service_name }}",
      JWT_ACCESS_TOKEN_SECONDS: 1800,
    });
  });

  it("reads process environment when auth is configured", async () => {
    vi.stubEnv("JWT_SECRET", TEST_SECRET);
    vi.stubEnv("JWT_ALGORITHM", "HS256");
    vi.stubEnv("JWT_ISSUER", "test-issuer");
    vi.stubEnv("JWT_ACCESS_TOKEN_SECONDS", "60");
    expect(loadJwtConfig().JWT_ISSUER).toBe("test-issuer");
    const auth = createJwtAuth();
    expect(await auth.verifyAccessToken(await auth.createAccessToken("user-123"))).toEqual({
      subject: "user-123",
      tokenType: "access",
    });
  });

  it.each([undefined, "", "too-short", " ".repeat(32)])(
    "rejects an absent or weak secret: %s",
    (secret) => {
      expect(() => createJwtAuth({ JWT_SECRET: secret })).toThrow();
    },
  );

  it.each(["none", "HS384", "RS256"])("rejects unsupported algorithms: %s", (algorithm) => {
    expect(() =>
      createJwtAuth({
        JWT_SECRET: TEST_SECRET,
        JWT_ALGORITHM: algorithm,
      }),
    ).toThrow();
  });

  it.each(["0", "-1", "1.5", "invalid", ""])("rejects an invalid lifetime: %s", (lifetime) => {
    expect(() =>
      createJwtAuth({
        JWT_SECRET: TEST_SECRET,
        JWT_ACCESS_TOKEN_SECONDS: lifetime,
      }),
    ).toThrow();
  });

  it("rejects a blank issuer", () => {
    expect(() => createJwtAuth({ JWT_SECRET: TEST_SECRET, JWT_ISSUER: " " })).toThrow();
  });
});
