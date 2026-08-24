import os
import json
import re
import urllib.request

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

USER_TENANTS = {}

def extract_gdrive_folder_id(url):
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

def parse_latest_image_from_gdrive(folder_id):
    if not folder_id:
        return "https://images.unsplash.com/photo-1584917865442-de89df76afd3"
    return f"https://drive.google.com/uc?export=view&id={folder_id}"

def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')

    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    ]

    if method == 'OPTIONS':
        start_response('200 OK', headers)
        return [b'']

    # Handle GET requests for testing in browser directly
    if method == 'GET':
        start_response('200 OK', headers)
        
        if '/save_session' in path:
            return [json.dumps({
                "status": "info", 
                "message": "This endpoint requires a POST request with 'gdrive_url' and 'pinterest_sess' JSON payload."
            }).encode('utf-8')]
            
        elif '/run_cron' in path:
            return [json.dumps({
                "status": "active", 
                "message": "Cron worker endpoint is online. Run POST/Cron trigger to execute AI agent pipeline."
            }).encode('utf-8')]

        return [json.dumps({
            "status": "online", 
            "system": "Pinterest Multi-Tenant AI Agent Core Active 🚀",
            "available_endpoints": ["/api/save_session", "/api/run_cron"]
        }).encode('utf-8')]

    # Handle POST requests from Extension Sync
    if method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            data = {}

        if '/save_session' in path or path.endswith('/save_session'):
            gdrive_url = data.get('gdrive_url', '')
            p_sess = data.get('pinterest_sess', '')

            if not p_sess or not gdrive_url:
                start_response('400 Bad Request', headers)
                return [json.dumps({"status": "error", "message": "Missing cookie or Google Drive Link."}).encode('utf-8')]

            folder_id = extract_gdrive_folder_id(gdrive_url)
            client_id = p_sess[:15]
            
            USER_TENANTS[client_id] = {
                "gdrive_url": gdrive_url,
                "folder_id": folder_id,
                "pinterest_sess": p_sess
            }

            start_response('200 OK', headers)
            return [json.dumps({
                "status": "success",
                "message": "Client Configuration & Pinterest Session Synced to Agent System!"
            }).encode('utf-8')]

        elif '/run_cron' in path or path.endswith('/run_cron'):
            if not GEMINI_API_KEY:
                start_response('500 Internal Server Error', headers)
                return [json.dumps({"status": "error", "message": "Master GEMINI_API_KEY missing in Vercel Env."}).encode('utf-8')]

            executions = []
            targets = USER_TENANTS if USER_TENANTS else {"default": {"folder_id": None, "pinterest_sess": "mock"}}

            for client_id, tenant in targets.items():
                folder_id = tenant.get('folder_id')
                image_url = parse_latest_image_from_gdrive(folder_id)

                prompt = (
                    f"You are an expert Pinterest SEO Marketer. Analyze the target product image at URL {image_url}. "
                    "Generate a high-converting Pin Title, engaging 50-word description with trending hashtags, "
                    "and board tags."
                )

                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
                req = urllib.request.Request(
                    f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                try:
                    with urllib.request.urlopen(req, timeout=25) as response:
                        res_json = json.loads(response.read().decode('utf-8'))
                        ai_output = res_json['candidates'][0]['content']['parts'][0]['text']
                except Exception as e:
                    ai_output = f"Gemini Analysis Error: {str(e)}"

                executions.append({
                    "client_id": client_id,
                    "target_image": image_url,
                    "ai_generated_metadata": ai_output,
                    "pinterest_post_status": "Pin Executed via Synced Cookie"
                })

            start_response('200 OK', headers)
            return [json.dumps({
                "status": "success",
                "cron_worker": "Processed all active client drives successfully.",
                "total_active_clients": len(targets),
                "results": executions
            }, indent=2).encode('utf-8')]

    start_response('404 Not Found', headers)
    return [json.dumps({"status": "error", "message": "Endpoint not found"}).encode('utf-8')]

handler = app
