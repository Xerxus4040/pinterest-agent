import { NextResponse } from "next/server";
import { createStudent, listStudents } from "@/lib/store";

export async function GET() {
  return NextResponse.json({ students: listStudents() });
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const name = String(body.name ?? "").trim();
    const driveUrl = String(body.driveUrl ?? "").trim();

    if (!name || !driveUrl) {
      return NextResponse.json(
        { error: "name and driveUrl are required" },
        { status: 400 }
      );
    }

    const student = createStudent({
      id: crypto.randomUUID(),
      name,
      driveUrl,
      active: body.active !== false,
      mode: body.mode === "auto" ? "auto" : "approval",
      postsPerDay: Math.max(1, Number(body.postsPerDay ?? 1)),
      postHour: Math.min(23, Math.max(0, Number(body.postHour ?? 20))),
      timezone: String(body.timezone ?? "Asia/Karachi"),
      processedSourceIds: [],
      createdAt: new Date().toISOString(),
    });

    return NextResponse.json({ student }, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unable to create student" },
      { status: 500 }
    );
  }
}
