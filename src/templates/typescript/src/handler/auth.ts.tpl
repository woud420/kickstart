import { SignJWT, jwtVerify, type JWTPayload } from "jose";

const encoder = new TextEncoder();

export interface AccessTokenClaims extends JWTPayload {
  sub: string;
}

export function createSecretKey(secret: string): Uint8Array {
  return encoder.encode(secret);
}

export async function createAccessToken(
  subject: string,
  secret: string,
  issuer: string,
): Promise<string> {
  return new SignJWT({})
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(subject)
    .setIssuer(issuer)
    .setIssuedAt()
    .setExpirationTime("15m")
    .sign(createSecretKey(secret));
}

export async function verifyAccessToken(
  token: string,
  secret: string,
  issuer: string,
): Promise<AccessTokenClaims> {
  const { payload } = await jwtVerify(token, createSecretKey(secret), { issuer });

  if (typeof payload.sub !== "string") {
    throw new Error("JWT subject is required");
  }

  return payload as AccessTokenClaims;
}
