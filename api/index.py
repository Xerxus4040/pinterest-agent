import os
import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler

# Environment Variable from Vercel Dashboard
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Correct Standard Stable Gemini API Endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

USER_TENANTS = {}

def extract_folder_id(drive_url):
    """Extracts Folder ID from Google Drive URLs"""
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)
    match_id = re.search(r'id=([a-zA-Z0-9_-]+)', drive_url)
    if match_id:
        return match_id.group(1)
    return drive_url

def call_gemini_text(prompt_text):
    """Calls Gemini 1.5 Flash API to generate Pinterest SEO Content"""
    if not GEMINI_API_KEY:
        return {
            "status": "error", 
            "message": "GEMINI_API_KEY is missing in Vercel Environment Variables. Add it in Vercel Settings -> Environment Variables and redeploy."
        }

    formatted_prompt = (
        f"Create a high-converting Pinterest Pin SEO metadata for topic: '{prompt_text}'. "
        "Return strictly valid raw JSON only without markdown formatting like ```json. "
        "JSON structure must be: "
        "{\"title\": \"Catchy title under 100 chars\", "
        "\"description\": \"Engaging description under 500 chars with CTA\", "
        "\"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\"]}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": formatted_prompt}
                ]
            }
        ]
    }

    req = urllib.request.Request(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            ai_raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            
            # Clean Markdown formatting wrappers if Gemini returns them
            cleaned_text = ai_raw_
