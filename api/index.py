import os
import json
import base64
import urllib.request
from http.server import BaseHTTPRequestHandler

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

USER_TENANTS = {}

def call_gemini_text(prompt_text):
    """Simple text prompt call to Gemini Flash"""
    if not GEMINI_API_KEY:
        return {"status": "error", "message": "GEMINI_API_KEY missing in Vercel Environment Variables."}

    payload = {
        "contents": [{"parts": [{"text": f"Generate a high-converting Pinterest Pin title, description, and hashtags for: '{prompt_text}'. Return strictly raw JSON in this format: {{\\\"title\\\": \\\"...\\\", \\\"description\\\": \\\"...\\\", \\\"hashtags\\\": [\\\"#...\\\"]}}"}]}]
    }

    req = urllib.request.Request(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            ai_raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            cleaned_text = ai_raw_text.replace('```json', '').replace('```', '').strip()
            return {"status": "success", "data": json.loads(cleaned_text)}
    except Exception as e:
        return {"status": "error", "message": f"Gemini API Error: {str(e)}"}

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
        self.wfile.write(json.dumps({"status": "success", "message": "Pinterest AI Backend Live"}).encode('utf-8'))

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

        # Action 1: Save Extension Session & Drive
        if action == 'save_session' or (gdrive and sess):
            USER_TENANTS['user_main'] = {"gdrive_url": gdrive, "pinterest_sess": sess}
            res = {"status": "success", "message": "Data Synced to Vercel Server"}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # Action 2: Test Gemini AI Generation
        if action == 'generate_metadata' or prompt:
            test_prompt = prompt if prompt else "Modern living room home decor ideas"
            ai_res = call_gemini_text(test_prompt)
            self.wfile.write(json.dumps(ai_res).encode('utf-8'))
            return

        # Fallback if no valid parameters provided
        res = {"status": "error", "message": "Invalid request. Provide 'action' or required fields."}
        self.wfile.write(json.dumps(res).encode('utf-8'))
