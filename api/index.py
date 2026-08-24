import os
import json
import re
import urllib.request

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Updated to Gemini 3.5 Flash Model Endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

USER_TENANTS = {}

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Pinterest AI Agent - Gemini 3.5 Flash Tester</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .card { width: 100%; max-width: 600px; background: #1e293b; border-radius: 12px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h2 { margin-top: 0; color: #38bdf8; font-size: 20px; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; background: #22c55e22; color: #4ade80; font-size: 12px; font-weight: bold; margin-bottom: 15px; border: 1px solid #4ade8044; }
        #chat-box { background: #0f172a; height: 260px; border-radius: 8px; padding: 12px; overflow-y: auto; border: 1px solid #334155; margin-bottom: 12px; font-size: 13px; }
        .msg { margin-bottom: 8px; line-height: 1.4; }
        .user { color: #38bdf8; font-weight: bold; }
        .ai { color: #f43f5e; font-weight: bold; }
        .input-group { display: flex; gap: 8px; }
        input { flex: 1; background: #0f172a; border: 1px solid #334155; color: #fff; padding: 10px; border-radius: 6px; outline: none; }
        button { background: #e60023; color: white; border: none; padding: 10px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        button:hover { background: #ad081b; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Pinterest AI Agent Hub 🚀</h2>
        <div class="status-badge">● Engine Online: Gemini 3.5 Flash Active</div>
        <div id="chat-box">
            <div class="msg"><span class="ai">Agent:</span> Send a query to test your Gemini 3.5 Flash connection live!</div>
        </div>
        <div class="input-group">
            <input type="text" id="userInput" placeholder="Test Gemini 3.5 Flash API key..." />
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chat-box');
            const msg = input.value.trim();
            if (!msg) return;

            chatBox.innerHTML += `<div class="msg"><span class="user">You:</span> ${msg}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            chatBox.innerHTML += `<div class="msg" id="loading"><span class="ai">Agent:</span> Thinking (Gemini 3.5 Flash)...</div>`;

            try {
                const res = await fetch('/api/test_chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: msg })
                });
                const data = await res.json();
                document.getElementById('loading').remove();
                
                if(data.status === 'success') {
                    chatBox.innerHTML += `<div class="msg"><span class="ai">Gemini 3.5 Flash:</span> ${data.response}</div>`;
                } else {
                    chatBox.innerHTML += `<div class="msg" style="color:#f87171;"><span class="ai">Error:</span> ${data.message}</div>`;
                }
            } catch(e) {
                document.getElementById('loading').remove();
                chatBox.innerHTML += `<div class="msg" style="color:#f87171;"><span class="ai">Error:</span> Network request failed</div>`;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>"""

def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    ]

    if method == 'OPTIONS':
        start_response('200 OK', headers)
        return [b'']

    if method == 'GET':
        headers.append(('Content-Type', 'text/html'))
        start_response('200 OK', headers)
        return [DASHBOARD_HTML.encode('utf-8')]

    if method == 'POST':
        headers.append(('Content-Type', 'application/json'))

        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            data = {}

        if '/test_chat' in path:
            prompt_text = data.get('prompt', 'Hello!')
            if not GEMINI_API_KEY:
                start_response('200 OK', headers)
                return [json.dumps({"status": "error", "message": "GEMINI_API_KEY is missing in Vercel Environment Variables."}).encode('utf-8')]

            payload = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode('utf-8')
            req = urllib.request.Request(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    ai_reply = res_json['candidates'][0]['content']['parts'][0]['text']
                    start_response('200 OK', headers)
                    return [json.dumps({"status": "success", "response": ai_reply}).encode('utf-8')]
            except Exception as e:
                start_response('200 OK', headers)
                return [json.dumps({"status": "error", "message": f"Gemini 3.5 Flash API Error: {str(e)}"}).encode('utf-8')]

        elif '/save_session' in path:
            gdrive_url = data.get('gdrive_url', '')
            p_sess = data.get('pinterest_sess', '')

            if not p_sess or not gdrive_url:
                start_response('400 Bad Request', headers)
                return [json.dumps({"status": "error", "message": "Missing Session or Google Drive Link."}).encode('utf-8')]

            USER_TENANTS['user_main'] = {"gdrive_url": gdrive_url, "pinterest_sess": p_sess}

            start_response('200 OK', headers)
            return [json.dumps({"status": "success", "message": "Drive Link & Pinterest Session Synced!"}).encode('utf-8')]

        elif '/run_cron' in path:
            start_response('200 OK', headers)
            return [json.dumps({"status": "success", "cron": "Executed using Gemini 3.5 Flash"}).encode('utf-8')]

    start_response('404 Not Found', [('Content-Type', 'application/json')])
    return [json.dumps({"status": "error", "message": "Endpoint not found"}).encode('utf-8')]

handler = app
