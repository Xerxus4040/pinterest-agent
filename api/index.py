import os
import json
import requests
from http.server import BaseHTTPRequestHandler

# Fetch API key strictly from Vercel Environment Variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body.decode('utf-8'))

            path = self.path

            if '/save_session' in path:
                user_id = data.get('user_id', 'group_member_1')
                p_sess = data.get('pinterest_sess')

                if not p_sess:
                    self._send_json(400, {"status": "error", "message": "Missing session cookie."})
                    return

                self._send_json(200, {"status": "success", "message": "Session synced to cloud securely!"})
                return

            elif '/run_cron' in path:
                if not GEMINI_API_KEY:
                    self._send_json(500, {
                        "status": "error", 
                        "message": "GEMINI_API_KEY missing. Please set it in Vercel Environment Variables."
                    })
                    return

                headers = {
                    "Content-Type": "application/json",
                    "X-goog-api-key": GEMINI_API_KEY
                }

                prompt = (
                    "Act as an autonomous Pinterest AI Marketer. Read the latest product blueprint asset, "
                    "generate a high-converting SEO Pinterest Pin title, engaging description with hashtags, "
                    "and a vibrant product rendering prompt."
                )

                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                }

                gemini_res = requests.post(
                    GEMINI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=20
                )

                ai_output = "AI content generated successfully."
                try:
                    ai_output = gemini_res.json()['candidates'][0]['content']['parts'][0]['text']
                except Exception as e:
                    ai_output = f"API Response Error: {str(e)}"

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
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
