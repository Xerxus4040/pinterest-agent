import os
import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler
from google import genai

# Environment Variables from Vercel Dashboard
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
NANO_BANANA_API_KEY = os.environ.get('NANO_BANANA_API_KEY', '')
# Replace with your actual Nano Banana / Image Model Endpoint
NANO_BANANA_API_URL = os.environ.get('NANO_BANANA_API_URL', 'https://api.vyce.ai/v1/models/nano-banana/generate')

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

def generate_nano_banana_image(prompt, image_url=None):
    """
    Calls Nano Banana Model for Image Generation or Style Transfer.
    If NANO_BANANA_API_KEY is not set, falls back to the provided image_url.
    """
    if not NANO_BANANA_API_KEY:
        # Fallback if Nano Banana API key isn't provided: return input image or placeholder
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Nano+Banana+Image"

    payload = {
        "prompt": prompt,
        "aspect_ratio": "2:3",  # Pinterest optimal vertical ratio
        "init_image": image_url
    }

    req = urllib.request.Request(
        NANO_BANANA_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NANO_BANANA_API_KEY}"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('image_url', res.get('output', ''))
    except Exception as e:
        print(f"Nano Banana API Error: {str(e)}")
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Generation+Failed"

def generate_gemini_metadata(prompt_text):
    """Calls Gemini 3.7 Flash for SEO Metadata Generation"""
    if not GEMINI_API_KEY:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY missing in Vercel Environment Variables."
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        formatted_prompt = (
            f"Create high-converting Pinterest Pin SEO metadata for: '{prompt_text}'. "
            "Return strictly valid raw JSON only without markdown codeblocks or formatting. "
            "JSON structure: "
            "{\"title\": \"Catchy title under 100 chars\", "
            "\"description\": \"Engaging description under 500 chars with call to action\", "
            "\"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\"]}"
        )

        response = client.models.generate_content(
            model='gemini-3.7-flash',
            contents=formatted_prompt,
        )

        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        return {"status": "success", "data": json.loads(cleaned_text)}

    except Exception as e:
        return {"status": "error", "message": f"Gemini Error: {str(e)}"}

class handler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        res = {"status": "success", "message": "Dual-Engine Pipeline Ready (Nano Banana + Gemini 3.7 Flash)"}
        self.wfile.write(json.dumps(res).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'

        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}

        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        action = data.get('action', '')
        gdrive = data.get('gdrive_url', '').strip()
        sess = data.get('pinterest_sess', '').strip()
        prompt = data.get('prompt', '').strip()
        image_url = data.get('image_url', '').strip()

        # Action 1: Save Session & Drive
        if action == 'save_session' or (gdrive and sess):
            folder_id = extract_folder_id(gdrive)
            USER_TENANTS['user_main'] = {
                "gdrive_url": gdrive,
                "folder_id": folder_id,
                "pinterest_sess": sess
            }
            res = {
                "status": "success",
                "message": "Data Synced to Vercel Server",
                "folder_id": folder_id
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # Action 2: Multi-Model Processing (Nano Banana + Gemini 3.7 Flash)
        if action in ['generate_pin', 'generate_metadata'] or prompt:
            req_prompt = prompt if prompt else "Modern living room home decor"

            # 1. Image Generation via Nano Banana
            generated_img = generate_nano_banana_image(req_prompt, image_url)

            # 2. Text/SEO Generation via Gemini 3.7 Flash
            ai_seo = generate_gemini_metadata(req_prompt)

            if ai_seo.get("status") == "success":
                seo_data = ai_seo.get("data", {})
                res = {
                    "status": "success",
                    "pin_asset": {
                        "image_url": generated_img,
                        "title": seo_data.get("title", ""),
                        "description": seo_data.get("description", ""),
                        "hashtags": seo_data.get("hashtags", [])
                    }
                }
            else:
                res = ai_seo

            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        res = {"status": "error", "message": "Invalid Action Request"}
        self.wfile.write(json.dumps(res).encode('utf-8'))
