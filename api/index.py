import os
import json
import re
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Environment Variables from Vercel Dashboard
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
NANO_BANANA_API_KEY = os.environ.get('NANO_BANANA_API_KEY', '')
NANO_BANANA_API_URL = os.environ.get('NANO_BANANA_API_URL', 'https://api.vyce.ai/v1/models/nano-banana/generate')

# Direct REST Endpoint for Gemini 3.7 Flash
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent"

USER_TENANTS = {}

# ---------------------------------------------------------
# 1. Google Drive Helper
# ---------------------------------------------------------
def extract_folder_id(drive_url):
    """Extracts Folder ID from Google Drive URLs"""
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)
    match_id = re.search(r'id=([a-zA-Z0-9_-]+)', drive_url)
    if match_id:
        return match_id.group(1)
    return drive_url

# ---------------------------------------------------------
# 2. Nano Banana Model Generator
# ---------------------------------------------------------
def generate_nano_banana_image(prompt, image_url=None):
    """Calls Nano Banana API for image generation or falls back gracefully"""
    if not NANO_BANANA_API_KEY:
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Nano+Banana+Image"

    payload = {
        "prompt": prompt,
        "aspect_ratio": "2:3",
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
        with urllib.request.urlopen(req, timeout=25) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('image_url', res.get('output', ''))
    except Exception:
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Generation+Failed"

# ---------------------------------------------------------
# 3. Gemini 3.7 Flash SEO Metadata Generator
# ---------------------------------------------------------
def generate_gemini_metadata(prompt_text):
    """Calls Gemini 3.7 Flash REST API for SEO text and hashtags"""
    if not GEMINI_API_KEY:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY missing in Vercel Environment Variables."
        }

    formatted_prompt = (
        f"Create high-converting Pinterest Pin SEO metadata for: '{prompt_text}'. "
        "Return strictly valid raw JSON only without markdown formatting. "
        "JSON structure: "
        "{\"title\": \"Catchy title under 100 chars\", "
        "\"description\": \"Engaging description under 500 chars with CTA\", "
        "\"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\"]}"
    )

    payload = {
        "contents": [{"parts": [{"text": formatted_prompt}]}]
    }

    req = urllib.request.Request(
        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            ai_raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            cleaned_text = ai_raw_text.replace('```json', '').replace('```', '').strip()
            return {"status": "success", "data": json.loads(cleaned_text)}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8') if e.fp else str(e)
        return {"status": "error", "message": f"Gemini HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"status": "error", "message": f"Gemini REST Error: {str(e)}"}

# ---------------------------------------------------------
# 4. Pinterest Direct Session Cookie Publisher
# ---------------------------------------------------------
def create_pinterest_pin_via_session(session_cookie, board_id, image_url, title, description, link=""):
    """Posts a pin directly using internal web endpoint and _pinterest_sess cookie"""
    url = "https://www.pinterest.com/resource/PinResource/create/"

    resource_data = {
        "options": {
            "board_id": board_id,
            "image_url": image_url,
            "title": title,
            "description": description,
            "link": link,
            "scrape_metric": {"source": "upload"}
        },
        "context": {}
    }

    post_data = urllib.parse.urlencode({
        "data": json.dumps(resource_data)
    }).encode('utf-8')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": f"_pinterest_sess={session_cookie};"
    }

    req = urllib.request.Request(url, data=post_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            if res_body.get("resource_response", {}).get("error") is None:
                pin_id = res_body.get("resource_response", {}).get("data", {}).get("id")
                return {
                    "status": "success",
                    "pin_id": pin_id,
                    "pin_url": f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else ""
                }
            else:
                err = res_body.get("resource_response", {}).get("error", {}).get("message", "Unknown Pinterest error")
                return {"status": "error", "message": f"Pinterest API Error: {err}"}
    except Exception as e:
        return {"status": "error", "message": f"Posting Error: {str(e)}"}

# ---------------------------------------------------------
# 5. Main Handler Server
# ---------------------------------------------------------
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
        res = {"status": "success", "message": "All Systems Go (Nano Banana + Gemini 3.7 Flash + Direct Poster)"}
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
        board_id = data.get('board_id', '').strip()

        # ACTION 1: Extension Session & Drive Link Save
        if action == 'save_session' or (gdrive and sess and not action):
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

        # ACTION 2: Nano Banana + Gemini 3.7 Flash Asset Generation Test
        if action in ['generate_pin', 'generate_metadata']:
            req_prompt = prompt if prompt else "Modern living room home decor"
            generated_img = generate_nano_banana_image(req_prompt, image_url)
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

        # ACTION 3: Direct Publish via Cookie
        if action == 'publish_pin':
            if not sess or not board_id or not image_url:
                res = {"status": "error", "message": "Missing fields: pinterest_sess, board_id, image_url"}
            else:
                res = create_pinterest_pin_via_session(
                    session_cookie=sess,
                    board_id=board_id,
                    image_url=image_url,
                    title=data.get('title', ''),
                    description=data.get('description', '')
                )
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # ACTION 4: FULL PIPELINE (Drive Image -> Gemini 3.7 Flash -> Nano Banana -> Pinterest Direct Post)
        if action == 'pipe_drive_to_pinterest' or prompt:
            req_prompt = prompt if prompt else "Modern Home Decor"

            if not sess or not board_id or not image_url:
                res = {
                    "status": "error",
                    "message": "Missing required fields for full pipeline: pinterest_sess, board_id, image_url"
                }
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return

            # Step A: Image via Nano Banana
            final_img = generate_nano_banana_image(req_prompt, image_url)

            # Step B: SEO via Gemini 3.7 Flash
            ai_res = generate_gemini_metadata(req_prompt)
            if ai_res.get("status") != "success":
                self.wfile.write(json.dumps(ai_res).encode('utf-8'))
                return

            seo_data = ai_res.get("data", {})
            title = seo_data.get("title", "")
            hashtags = " ".join(seo_data.get("hashtags", []))
            full_description = f"{seo_data.get('description', '')}\n\n{hashtags}".strip()

            # Step C: Direct Post to Pinterest
            post_res = create_pinterest_pin_via_session(
                session_cookie=sess,
                board_id=board_id,
                image_url=final_img,
                title=title,
                description=full_description
            )

            res = {
                "status": post_res.get("status"),
                "pipeline": {
                    "image_url": final_img,
                    "title": title,
                    "description": full_description,
                    "target_board_id": board_id,
                    "result": post_res
                }
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        res = {"status": "error", "message": "Invalid Action Request"}
        self.wfile.write(json.dumps(res).encode('utf-8'))
