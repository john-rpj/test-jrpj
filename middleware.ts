import { createRemoteJWKSet, jwtVerify } from "jose";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const CF_TEAM_NAME = process.env.CF_TEAM_NAME ?? "";
const BYPASS_CF_AUTH = process.env.BYPASS_CF_AUTH === "true";

// Refuse to serve traffic with bypass enabled in production.
if (BYPASS_CF_AUTH && process.env.APP_ENV === "production") {
  throw new Error(
    "BYPASS_CF_AUTH must not be enabled in production (APP_ENV=production)"
  );
}

// Lazily initialised JWKS — cached for the lifetime of the edge function.
let JWKS: ReturnType<typeof createRemoteJWKSet> | null = null;

function getCfJwks() {
  if (!JWKS) {
    if (!CF_TEAM_NAME) {
      throw new Error("CF_TEAM_NAME env var is required for JWT verification");
    }
    JWKS = createRemoteJWKSet(
      new URL(
        `https://${CF_TEAM_NAME}.cloudflareaccess.com/cdn-cgi/access/certs`
      )
    );
  }
  return JWKS;
}

export async function middleware(request: NextRequest) {
  if (BYPASS_CF_AUTH) {
    const response = NextResponse.next();
    response.headers.set(
      "x-user-email",
      process.env.DEV_USER_EMAIL ?? "dev@local"
    );
    return response;
  }

  const cfJwt = request.headers.get("cf-access-jwt-assertion");
  if (!cfJwt) {
    return new NextResponse("Unauthorized", { status: 401 });
  }

  try {
    const { payload } = await jwtVerify(cfJwt, getCfJwks());
    const email =
      typeof payload.email === "string" ? payload.email : "unknown";
    const response = NextResponse.next();
    response.headers.set("x-user-email", email);
    return response;
  } catch {
    return new NextResponse("Unauthorized", { status: 401 });
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|health).*)"],
};
