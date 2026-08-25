import {GoogleGenAI} from "@google/genai";
export function ai(){const k=process.env.GEMINI_API_KEY;if(!k)throw new Error("GEMINI_API_KEY missing");return new GoogleGenAI({apiKey:k})}
export const TEXT_MODEL="gemini-2.5-flash";
export const IMAGE_MODEL="gemini-3.1-flash-image";
