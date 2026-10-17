import { decodeJwt, decodeProtectedHeader, SignJWT, type JWTPayload } from "jose";
import { describe, expect, it } from "vitest";

import { createJwtAuth } from "../src/handler/auth.js";

const TEST_SECRET = "test-only-jwt-secret-with-at-least-64-characters-for-algorithm-tests";
const TEST_ISSUER = "test-issuer";
const environment = { JWT_SECRET: TEST_SECRET, JWT_ISSUER: TEST_ISSUER };
const auth = createJwtAuth(environment);

function validClaims(): JWTPayload {
  const now = Math.floor(Date.now() / 1000);
  return {
    sub: "user-123",
    type: "access",
    iss: TEST_ISSUER,
    iat: now,
    exp: now + 60,
  };
}

async function signedToken(
  claims: JWTPayload,
  algorithm = "HS256",
  tokenType = "JWT",
): Promise<string> {
  return new SignJWT(claims)
    .setProtectedHeader({ alg: algorithm, typ: tokenType })
    .sign(new TextEncoder().encode(TEST_SECRET));
}

describe("JWT auth", () => {
  it("creates and verifies an expiring access token for the configured issuer", async () => {
    const token = await auth.createAccessToken("user-123");
    const payload = decodeJwt(token);

    expect(decodeProtectedHeader(token)).toEqual({
      alg: "HS256",
      typ: "JWT",
    });
    expect(payload).toMatchObject({
      sub: "user-123",
      type: "access",
      iss: TEST_ISSUER,
    });
    expect(payload.iat).toBeGreaterThan(0);
    expect(payload.exp).toBe((payload.iat ?? 0) + 1800);
    expect(await auth.verifyAccessToken(token)).toEqual({
      subject: "user-123",
      tokenType: "access",
    });
  });

  it("honors the configured lifetime", async () => {
    const shortLived = createJwtAuth({
      ...environment,
      JWT_ACCESS_TOKEN_SECONDS: "60",
    });
    const payload = decodeJwt(await shortLived.createAccessToken("user-123"));
    expect(payload.iat).toBeGreaterThan(0);
    expect(payload.exp).toBe((payload.iat ?? 0) + 60);
  });

  it("rejects malformed and tampered tokens", async () => {
    const token = await auth.createAccessToken("user-123");
    expect(await auth.verifyAccessToken("not-a-token")).toBeNull();
    expect(await auth.verifyAccessToken(token + "tampered")).toBeNull();
  });

  it("rejects tokens signed with another secret or issued by another service", async () => {
    const other = createJwtAuth({
      ...environment,
      JWT_SECRET: "different-test-only-secret-at-least-32-characters",
    });
    expect(await other.verifyAccessToken(await auth.createAccessToken("user-123"))).toBeNull();
    const otherIssuer = createJwtAuth({
      ...environment,
      JWT_ISSUER: "other-service",
    });
    expect(
      await otherIssuer.verifyAccessToken(await auth.createAccessToken("user-123")),
    ).toBeNull();
  });

  it.each(["sub", "type", "iss", "iat", "exp"])("requires the %s claim", async (claim) => {
    const claims = validClaims();
    delete claims[claim];
    expect(await auth.verifyAccessToken(await signedToken(claims))).toBeNull();
  });

  it("rejects expired, not-yet-valid and future-issued tokens", async () => {
    const claims = validClaims();
    const now = Math.floor(Date.now() / 1000);
    for (const invalid of [
      { ...claims, exp: now - 1 },
      { ...claims, nbf: now + 60 },
      { ...claims, iat: now + 60 },
    ]) {
      expect(await auth.verifyAccessToken(await signedToken(invalid))).toBeNull();
    }
  });

  it("enforces the configured maximum age even when expiry is further away", async () => {
    const shortLived = createJwtAuth({
      ...environment,
      JWT_ACCESS_TOKEN_SECONDS: "60",
    });
    const claims = {
      ...validClaims(),
      iat: Math.floor(Date.now() / 1000) - 120,
    };
    expect(await shortLived.verifyAccessToken(await signedToken(claims))).toBeNull();
  });

  it("rejects unsigned tokens", async () => {
    const header = Buffer.from(JSON.stringify({ alg: "none", typ: "JWT" })).toString("base64url");
    const payload = Buffer.from(JSON.stringify(validClaims())).toString("base64url");
    expect(await auth.verifyAccessToken(`${header}.${payload}.`)).toBeNull();
  });

  it("rejects the wrong algorithm, header type or payload token type", async () => {
    expect(await auth.verifyAccessToken(await signedToken(validClaims(), "HS384"))).toBeNull();
    expect(
      await auth.verifyAccessToken(await signedToken(validClaims(), "HS256", "refresh+jwt")),
    ).toBeNull();
    expect(
      await auth.verifyAccessToken(await signedToken({ ...validClaims(), type: "refresh" })),
    ).toBeNull();
  });

  it("rejects blank subjects when signing or verifying", async () => {
    await expect(auth.createAccessToken(" ")).rejects.toThrow(TypeError);
    expect(
      await auth.verifyAccessToken(await signedToken({ ...validClaims(), sub: " " })),
    ).toBeNull();
  });
});
