import os
import json
import re
import time
import random
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Environment Variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
NANO_BANANA_API_KEY = os.environ.get('NANO_BANANA_API_KEY', '')
NANO_BANANA_API_URL = os.environ.get('NANO_BANANA_API_URL', 'https://api.vyce.ai/v1/models/nano-banana/generate')

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent"

# Multi-tenant user session cache (IP or Token based)
USER_TENANTS = {}

# ---------------------------------------------------------
# 1. Drive Helper
# ---------------------------------------------------------
def extract_folder_id(drive_url):
    match = re.search(r'folders/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)
    match_id = re.search(r'id=([a-zA-Z0-9_-]+)', drive_url)
    if match_id:
        return match_id.group(1)
    return drive_url

# ---------------------------------------------------------
# 2. Nano Banana Image Generator (Sketch to Colourful Image)
# ---------------------------------------------------------
def generate_nano_banana_image(prompt, image_url=None):
    if not NANO_BANANA_API_KEY:
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Nano+Banana+Image"

    payload = {
        "prompt": f"Turn this sketch into a colorful, highly detailed, realistic aesthetic Pinterest image: {prompt}",
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
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get('image_url', res.get('output', image_url))
    except Exception:
        return image_url if image_url else "https://via.placeholder.com/1000x1500.png?text=Generation+Failed"

# ---------------------------------------------------------
# 3. Gemini 3.7 Flash SEO Generator
# ---------------------------------------------------------
def generate_gemini_metadata(prompt_text):
    if not GEMINI_API_KEY:
        return {"status": "error", "message": "GEMINI_API_KEY missing"}

    formatted_prompt = (
        f"Create high-converting Pinterest Pin SEO metadata for: '{prompt_text}'. "
        "Return strictly valid raw JSON only without markdown formatting. "
        "JSON structure: "
        "{\"title\": \"Catchy title under 100 chars\", "
        "\"description\": \"Engaging description under 500 chars with CTA\", "
        "\"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\"]}"
    )

    payload = {"contents": [{"parts": [{"text": formatted_prompt}]}]}

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
    except Exception as e:
        return {"status": "error", "message": f"Gemini REST Error: {str(e)}"}

# ---------------------------------------------------------
# 4. Pinterest Session Validator & Direct Publisher
# ---------------------------------------------------------
def check_pinterest_session_validity(session_cookie):
    """Checks if the saved _pinterest_sess cookie is active or expired"""
    url = "https://www.pinterest.com/resource/UserResource/get/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"_pinterest_sess={session_cookie};"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get("resource_response", {}).get("error") is None:
                return True
            return False
    except Exception:
        return False

def create_pinterest_pin_via_session(session_cookie, board_id, image_url, title, description, link=""):
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

    post_data = urllib.parse.urlencode({"data": json.dumps(resource_data)}).encode('utf-8')

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
                if "authorization" in err.lower() or "login" in err.lower():
                    return {"status": "cookie_expired", "message": "Pinterest Session Cookie Expired!"}
                return {"status": "error", "message": f"Pinterest API Error: {err}"}
    except Exception as e:
        return {"status": "error", "message": f"Posting Error: {str(e)}"}

# ---------------------------------------------------------
# 5. Handler Engine
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
        res = {"status": "success", "message": "All Engines Active (Anti-Bot + Cookie Validator Included)"}
        self.wfile.write(json.dumps(res).encode('utf-8'))

    def do_POST(self):
        client_ip = self.headers.get('X-Forwarded-For', self.client_address[0]).split(',')[0].strip()
        
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
        board_id = data.get('board_id', '').strip()
        images_batch = data.get('images_batch', []) # List of direct Drive Sketch image URLs

        # 1. Save Multi-tenant Session by Client IP
        if action == 'save_session' or (gdrive and sess and not action):
            folder_id = extract_folder_id(gdrive)
            USER_TENANTS[client_ip] = {
                "gdrive_url": gdrive,
                "folder_id": folder_id,
                "pinterest_sess": sess
            }
            
            # Check Cookie Health immediately
            is_valid = check_pinterest_session_validity(sess)
            
            res = {
                "status": "success",
                "client_ip": client_ip,
                "folder_id": folder_id,
                "cookie_status": "active" if is_valid else "expired_or_invalid"
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 2. Check Session Cookie Health Status
        if action == 'validate_cookie':
            is_valid = check_pinterest_session_validity(sess)
            res = {"status": "success", "is_valid": is_valid}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # 3. Batch Auto-Posting with Anti-Bot Random Delays
        if action == 'batch_process_drive':
            if not sess or not board_id or not images_batch:
                res = {"status": "error", "message": "Missing fields: pinterest_sess, board_id, images_batch"}
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return

            # Check Cookie first
            if not check_pinterest_session_validity(sess):
                res = {"status": "cookie_expired", "message": "Pinterest Session Cookie is expired. Please sync extension."}
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return

            results = []
            total_items = len(images_batch)

            for idx, raw_image in enumerate(images_batch):
                req_prompt = prompt if prompt else f"Creative Sketch Render {idx+1}"

                # Step A: Nano Banana Sketch-to-Colourful Image
                colourful_img = generate_nano_banana_image(req_prompt, raw_image)

                # Step B: Gemini 3.7 Flash SEO Generation
                ai_res = generate_gemini_metadata(req_prompt)
                if ai_res.get("status") == "success":
                    seo_data = ai_res.get("data", {})
                    title = seo_data.get("title", "")
                    hashtags = " ".join(seo_data.get("hashtags", []))
                    full_desc = f"{seo_data.get('description', '')}\n\n{hashtags}".strip()
                else:
                    title = f"Sketch Design #{idx+1}"
                    full_desc = "Beautiful Sketch to Image Conversion #Art #Design"

                # Step C: Direct Post
                post_res = create_pinterest_pin_via_session(
                    session_cookie=sess,
                    board_id=board_id,
                    image_url=colourful_img,
                    title=title,
                    description=full_desc
                )

                results.append({
                    "item_index": idx + 1,
                    "sketch_url": raw_image,
                    "rendered_url": colourful_img,
                    "status": post_res.get("status"),
                    "pin_url": post_res.get("pin_url", "")
                })

                # Anti-Bot Protection Delay (If not last item)
                if idx < total_items - 1:
                    sleep_time = random.randint(30, 60) # 30 to 60 sec random wait
                    time.sleep(sleep_time)

            self.wfile.write(json.dumps({"status": "success", "processed_batch": results}).encode('utf-8'))
            return

        res = {"status": "error", "message": "Invalid Action Request"}
        self.wfile.write(json.dumps(res).encode('utf-8'))
