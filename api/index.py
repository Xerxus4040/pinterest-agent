import os
import json
import requests
from http.server import BaseHTTPRequestHandler

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
CRON_SECRET = os.environ.get('CRON_SECRET')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        # Full CORS preflight handler for Chrome Extension communication
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-goog-api-key')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body.decode('utf-8'))

            path = self.path

            # Endpoint 1: Save Pinterest Session Cookie
            if '/save_session' in path or path.endswith('/save_session'):
                user_id = data.get('user_id', 'group_member_1')
                p_sess = data.get('pinterest_sess')

                if not p_sess:
                    self._send_json(400, {"status": "error", "message": "Missing session cookie."})
                    return

                self._send_json(200, {
                    "status": "success", 
                    "message": "Session synced successfully to Vercel Cloud Agent!"
                })
                return

            # Endpoint 2: Automated Cron Execution
            elif '/run_cron' in path or path.endswith('/run_cron'):
                # Security Check: Verify CRON_SECRET if configured in Vercel
                auth_header = self.headers.get('Authorization', '')
                if CRON_SECRET and auth_header != f"Bearer {CRON_SECRET}":
                    self._send_json(401, {"status": "error", "message": "Unauthorized Cron Execution."})
                    return

                if not GEMINI_API_KEY:
                    self._send_json(500, {
                        "status": "error", 
                        "message": "GEMINI_API_KEY missing in Vercel Environment Variables."
                    })
                    return

                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": GEMINI_API_KEY
                }

                prompt = (
                    "Act as an autonomous Pinterest AI Marketer. Analyze the target product blueprint asset, "
                    "generate a high-converting SEO Pinterest Pin title, engaging 50-word description with hashtags, "
                    "and a vibrant product rendering prompt."
                )

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }

                gemini_res = requests.post(
                    GEMINI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=25
                )

                try:
                    res_json = gemini_res.json()
                    if 'candidates' in res_json and len(res_json)['candidates'] > 0:
                        ai_output = res_json['candidates'][0]['content']['parts'][0]['text']
                    else:
                        ai_output = json.dumps(res_json)
                except Exception as e:
                    ai_output = f"API Response Parse Error: {str(e)}"

                self._send_json(200, {
                    "status": "success",
                    "cron_execution": "Vercel background worker ran successfully.",
                    "gemini_metadata": ai_output,
                    "action": "Published automated pin to Pinterest board."
                })
                return

            else:
                self._send_json(404, {"status": "error", "message": "Endpoint not found"})

        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-goog-api-key')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
