export async function GET() {
  return Response.json({
    ok: true,
    service: "pinterest-ai-agent",
    timestamp: new Date().toISOString(),
  });
}
