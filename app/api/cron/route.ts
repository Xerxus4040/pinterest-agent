import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const secret = process.env.CRON_SECRET;
  const auth = request.headers.get("authorization");

  if (secret && auth !== `Bearer ${secret}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  // Phase 1: scheduler health check only.
  // Phase 2 will load due jobs from the database and enqueue AI/Pinterest work.
  return Response.json({
    ok: true,
    message: "Cron endpoint reached. Automation workers are not enabled yet.",
    timestamp: new Date().toISOString(),
  });
}
