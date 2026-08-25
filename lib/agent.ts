import { getGeminiClient, GEMINI_IMAGE_MODEL, GEMINI_TEXT_MODEL } from "@/lib/gemini";

type GeminiPart = {
  text?: string;
  inlineData?: { mimeType: string; data: string };
};

function extractText(response: any): string {
  if (typeof response?.text === "string" && response.text.trim()) return response.text.trim();
  const parts = (response?.candidates ?? []).flatMap((c: any) => c?.content?.parts ?? []);
  return parts.filter((p: GeminiPart) => typeof p.text === "string").map((p: GeminiPart) => p.text).join("\n").trim();
}

function extractGeneratedImage(response: any) {
  const parts = (response?.candidates ?? []).flatMap((c: any) => c?.content?.parts ?? []);
  for (const part of parts as GeminiPart[]) {
    if (part.inlineData?.data) {
      return { mimeType: part.inlineData.mimeType || "image/png", data: part.inlineData.data };
    }
  }
  return null;
}

export async function analyzeBlueprint(image: { mimeType: string; data: string }) {
  const ai = getGeminiClient();
  const response = await ai.models.generateContent({
    model: GEMINI_TEXT_MODEL,
    contents: [{
      role: "user",
      parts: [
        { inlineData: { mimeType: image.mimeType, data: image.data } },
        { text: `Analyze this architectural blueprint/sketch for Pinterest. Return JSON only:
{"title":"SEO Pinterest title","description":"Pinterest description","tags":["10-15 tags"],"altText":"accessible description","visualPrompt":"detailed premium architectural visualization prompt"}
Preserve important architectural characteristics and do not invent major structural features.` }
      ]
    }]
  });

  const text = extractText(response);
  if (!text) throw new Error("Gemini returned no analysis.");

  const cleaned = text.replace(/^```json\s*/i, "").replace(/\s*```$/i, "").trim();
  try { return JSON.parse(cleaned); }
  catch {
    return {
      title: "Modern House Design",
      description: text,
      tags: ["house design", "architecture", "home design", "blueprint"],
      altText: "Architectural house design based on a blueprint.",
      visualPrompt: text
    };
  }
}

export async function generatePinterestImage(
  sourceImage: { mimeType: string; data: string },
  visualPrompt: string
) {
  const ai = getGeminiClient();
  const response = await ai.models.generateContent({
    model: GEMINI_IMAGE_MODEL,
    contents: [{
      role: "user",
      parts: [
        { inlineData: { mimeType: sourceImage.mimeType, data: sourceImage.data } },
        { text: `${visualPrompt}
Create a premium Pinterest-ready architectural visualization using the supplied blueprint/sketch as structural reference. Keep the important layout and architectural intent recognizable. Make it polished, realistic and commercially appealing. No text, labels, watermarks, logos or UI. Compose vertically for Pinterest, approximately 2:3.` }
      ]
    }]
  });

  const image = extractGeneratedImage(response);
  if (!image) throw new Error("Gemini did not return a generated image.");
  return image;
}

export async function generatePinFromBlueprint(image: { mimeType: string; data: string }) {
  const analysis = await analyzeBlueprint(image);
  const generatedImage = await generatePinterestImage(image, analysis.visualPrompt);
  return { analysis, generatedImage };
}
