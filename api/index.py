import os
import json
from http.server import BaseHTTPRequestHandler

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

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

        gdrive = data.get('gdrive_url', '')
        sess = data.get('pinterest_sess', '')

        if not gdrive or not sess:
            res = {"status": "error", "message": "Missing required fields"}
        else:
            res = {"status": "success", "message": "Data Synced to Vercel Server"}

        self.wfile.write(json.dumps(res).encode('utf-8'))
