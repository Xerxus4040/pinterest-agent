import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

USER_TENANTS = {}

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"status": "online", "message": "Pinterest AI Agent Backend Running"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8')) if body else {}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Save session from Extension
        if 'save_session' in self.path:
            gdrive = data.get('gdrive_url')
            sess = data.get('pinterest_sess')
            USER_TENANTS['user_main'] = {"gdrive_url": gdrive, "pinterest_sess": sess}
            res = {"status": "success", "message": "Session & Drive Link Saved!"}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # Test Gemini AI Endpoint
        if 'test_chat' in self.path:
            prompt = data.get('prompt', 'Hello')
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
            req = urllib.request.Request(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    res_json = json.loads(resp.read().decode('utf-8'))
                    reply = res_json['candidates'][0]['content']['parts'][0]['text']
                    self.wfile.write(json.dumps({"status": "success", "response": reply}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        self.wfile.write(json.dumps({"status": "error", "message": "Invalid Route"}).encode('utf-8'))
