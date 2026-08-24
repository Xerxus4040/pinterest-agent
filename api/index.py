import os
import json
import urllib.request
import urllib.error

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
CRON_SECRET = os.environ.get('CRON_SECRET', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')

    # CORS Headers
    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-goog-api-key')
    ]

    # Handle OPTIONS Preflight
    if method == 'OPTIONS':
        start_response('200 OK', headers)
        return [b'']

    # 1. Root GET Route (Health Check)
    if method == 'GET':
        start_response('200 OK', headers)
        res = {
            "status": "online",
            "message": "Pinterest AI Agent Vercel Serverless Endpoint is Active 🚀"
        }
        return [json.dumps(res).encode('utf-8')]

    # 2. POST Routes
    if method == 'POST':
        try:
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0

            request_body = environ['wsgi.input'].read(request_body_size) if request_body_size > 0 else b'{}'
            data = json.loads(request_body.decode('utf-8')) if request_body else {}
        except Exception:
            data = {}

        # Save Session Endpoint
        if '/save_session' in path:
            p_sess = data.get('pinterest_sess')
            if not p_sess:
                start_response('400 Bad Request', headers)
                return [json.dumps({"status": "error", "message": "Missing session cookie."}).encode('utf-8')]

            start_response('200 OK', headers)
            return [json.dumps({
                "status": "success", 
                "message": "Session synced successfully to Vercel Cloud Agent!"
            }).encode('utf-8')]

        # Run Cron Endpoint
        elif '/run_cron' in path:
            if not GEMINI_API_KEY:
                start_response('500 Internal Server Error', headers)
                return [json.dumps({
                    "status": "error", 
                    "message": "GEMINI_API_KEY missing in Vercel Environment Variables."
                }).encode('utf-8')]

            prompt = (
                "Act as an autonomous Pinterest AI Marketer. Analyze the product, "
                "generate an SEO Pinterest Pin title and 50-word description with hashtags."
            )
            
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
            req = urllib.request.Request(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    ai_output = res_json['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                ai_output = f"Gemini Call Error: {str(e)}"

            start_response('200 OK', headers)
            return [json.dumps({
                "status": "success",
                "cron_execution": "Vercel background worker ran successfully.",
                "gemini_metadata": ai_output
            }).encode('utf-8')]

    start_response('404 Not Found', headers)
    return [json.dumps({"status": "error", "message": "Endpoint not found"}).encode('utf-8')]

# Entrypoint for Vercel
handler = app
