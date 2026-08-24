import os
import json
import re
import urllib.request
from http.server import BaseHTTPRequestHandler

# Environment Variable from Vercel Dashboard
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Standard Stable Gemini API Endpoint
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
            "message": "GEMINI_API_KEY is missing in Vercel Environment Variables."
        }

    formatted_prompt = (
        f"Create high-converting Pinterest Pin SEO metadata for topic: '{prompt_text}'. "
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
            
            cleaned_text = ai_raw_text.replace('```json', '').replace('```', '').strip()
            return {"status": "success", "data": json.loads(cleaned_text)}
            
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        return {"status": "error", "message": f"Gemini HTTP Error {e.code}: {err_body}"}
    except Exception as e:
        return {"status": "error", "message": f"Gemini Processing Error: {str(e)}"}

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
        res = {"status": "success", "message": "Pinterest AI Backend Online"}
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

        # Action 1: Extension Session Sync
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

        # Action 2: Gemini AI Content Generation
        if action == 'generate_metadata' or prompt:
            test_prompt = prompt if prompt else "Modern kitchen home decor"
            ai_res = call_gemini_text(test_prompt)
            self.wfile.write(json.dumps(ai_res).encode('utf-8'))
            return

        res = {
            "status": "error", 
            "message": "Invalid Request Action"
        }
        self.wfile.write(json.dumps(res).encode('utf-8'))
