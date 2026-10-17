import { errors, jwtVerify, SignJWT } from "jose";

import { loadJwtConfig } from "../config/env.js";

export interface VerifiedToken {
  subject: string;
  tokenType: "access";
}

export interface JwtAuth {
  createAccessToken(subject: string): Promise<string>;
  verifyAccessToken(token: string): Promise<VerifiedToken | null>;
}

export function createJwtAuth(environment: NodeJS.ProcessEnv = process.env): JwtAuth {
  const config = loadJwtConfig(environment);
  const key = new TextEncoder().encode(config.JWT_SECRET);

  return {
    async createAccessToken(subject: string): Promise<string> {
      if (subject.trim().length === 0) {
        throw new TypeError("Token subject must not be blank");
      }
      const now = Math.floor(Date.now() / 1000);
      return new SignJWT({ type: "access" })
        .setProtectedHeader({ alg: config.JWT_ALGORITHM, typ: "JWT" })
        .setSubject(subject)
        .setIssuer(config.JWT_ISSUER)
        .setIssuedAt(now)
        .setExpirationTime(now + config.JWT_ACCESS_TOKEN_SECONDS)
        .sign(key);
    },

    async verifyAccessToken(token: string): Promise<VerifiedToken | null> {
      try {
        const { payload } = await jwtVerify(token, key, {
          algorithms: [config.JWT_ALGORITHM],
          issuer: config.JWT_ISSUER,
          typ: "JWT",
          maxTokenAge: config.JWT_ACCESS_TOKEN_SECONDS,
          requiredClaims: ["sub", "type", "iat", "exp"],
        });
        if (
          typeof payload.sub !== "string" ||
          payload.sub.trim().length === 0 ||
          payload.type !== "access"
        ) {
          return null;
        }
        return { subject: payload.sub, tokenType: "access" };
      } catch (error) {
        if (error instanceof errors.JOSEError) {
          return null;
        }
        throw error;
      }
    },
  };
}
