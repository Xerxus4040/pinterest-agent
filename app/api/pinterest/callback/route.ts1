import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");

  if (!code) {
    return new Response("Missing Pinterest authorization code.", { status: 400 });
  }

  // TODO Phase 2:
  // 1. Validate OAuth state against the signed-in user.
  // 2. Exchange code at https://api.pinterest.com/v5/oauth/token.
  // 3. Encrypt/store access + refresh tokens in the database.
  // 4. Redirect to the Connections page.
  return Response.json({
    ok: true,
    message: "Pinterest callback received. Token exchange is the next implementation step.",
  });
}
