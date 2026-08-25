import { getGeminiClient, GEMINI_IMAGE_MODEL, GEMINI_TEXT_MODEL } from "@/lib/gemini";

type SourceImage = { mimeType: string; data: string };

function textFromResponse(response: any): string {
  if (typeof response?.text === "string" && response.text.trim()) return response.text.trim();
  const parts = response?.candidates?.flatMap((c: any) => c?.content?.parts ?? []) ?? [];
  return parts.filter((p: any) => typeof p.text === "string").map((p: any) => p.text).join("\n").trim();
}

function imageFromResponse(response: any): { mimeType: string; data: string } | null {
  const parts = response?.candidates?.flatMap((c: any) => c?.content?.parts ?? []) ?? [];
  for (const p of parts) {
    const d = p?.inlineData;
    if (d?.data) return { mimeType: d.mimeType || "image/png", data: d.data };
  }
  return null;
}

export async function analyzeBlueprint(image: SourceImage) {
  const ai = getGeminiClient();
  const response = await ai.models.generateContent({
    model: GEMINI_TEXT_MODEL,
    contents: [{
      role: "user",
      parts: [
        { inlineData: { mimeType: image.mimeType, data: image.data } },
        { text: `Analyze this blueprint/sketch for a Pinterest post. Return JSON only with:
title, description, tags (array of 10-15 strings), altText, visualPrompt.
Preserve the visible architectural intent and do not invent major structural features.` }
      ]
    }]
  });

  const raw = textFromResponse(response);
  if (!raw) throw new Error("Gemini returned no analysis.");
  const cleaned = raw.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "").trim();
  try { return JSON.parse(cleaned); }
  catch {
    return {
      title: "Modern House Design",
      description: raw,
      tags: ["house design", "architecture", "home design", "blueprint"],
      altText: "Architectural house design based on a blueprint.",
      visualPrompt: raw
    };
  }
}

export async function generatePinterestImage(image: SourceImage, visualPrompt: string) {
  const ai = getGeminiClient();

  // Gemini image generation returns image data in response candidates.
  // Use the current GenerateContent shape; no legacy `type`/`output_image` fields.
  const response = await ai.models.generateContent({
    model: GEMINI_IMAGE_MODEL,
    contents: [{
      role: "user",
      parts: [
        { inlineData: { mimeType: image.mimeType, data: image.data } },
        { text: `${visualPrompt}
Create a premium, photorealistic architectural visualization based on the supplied blueprint/sketch.
Keep the important layout and architectural intent recognizable.
No text, labels, watermarks, logos or UI. Vertical Pinterest composition, approximately 2:3.` }
      ]
    }]
  });

  const generated = imageFromResponse(response);
  if (!generated) throw new Error("Gemini did not return image data.");
  return generated;
}

export async function generatePinFromBlueprint(image: SourceImage) {
  const analysis = await analyzeBlueprint(image);
  const generatedImage = await generatePinterestImage(image, analysis.visualPrompt);
  return { analysis, generatedImage };
}
