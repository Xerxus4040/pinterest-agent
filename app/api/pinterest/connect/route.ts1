import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const clientId = process.env.PINTEREST_CLIENT_ID;
  const redirectUri = process.env.PINTEREST_REDIRECT_URI;

  if (!clientId || !redirectUri) {
    return Response.json(
      { ok: false, error: "Pinterest OAuth environment variables are missing." },
      { status: 500 }
    );
  }

  const state = crypto.randomUUID();
  const scope = "boards:read boards:write pins:read pins:write";

  const url = new URL("https://www.pinterest.com/oauth/");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", scope);
  url.searchParams.set("state", state);

  // TODO: Persist state against the signed-in user/session before redirecting.
  return Response.redirect(url);
}
