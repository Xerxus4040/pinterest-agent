import { getGeminiClient, GEMINI_TEXT_MODEL } from "@/lib/gemini";

export async function POST() {
  try {
    const ai = getGeminiClient();

    const response = await ai.models.generateContent({
      model: GEMINI_TEXT_MODEL,
      contents: "Reply with exactly: GEMINI_CONNECTION_OK",
    });

    return Response.json({ ok: true, text: response.text });
  } catch (error) {
    console.error(error);
    return Response.json(
      { ok: false, error: "Gemini connection failed." },
      { status: 500 }
    );
  }
}
