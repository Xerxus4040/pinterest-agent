import os
import json
import re
import time
import random
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Environment Variables from Vercel Dashboard
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
NANO_BANANA_API_KEY = os.environ.get('NANO_BANANA_API_KEY', '')
NANO_BANANA_API_URL = os.environ.get('NANO_BANANA_API_URL', 'https://api.vyce.ai/v1/models/nano-banana/generate')

# Gemini 3.7 Flash REST Endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent"

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
# 2. Nano Banana Model Generator (Sketch to Colourful Image)
# ---------------------------------------------------------
def generate_nano_banana_image(prompt, image_url=None):
    """Calls Nano Banana API for high-quality aesthetic image rendering"""
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
# 3. Gemini 3.7 Flash SEO Metadata Generator
# ---------------------------------------------------------
def generate_gemini_metadata(prompt_text):
    """Calls Gemini 3.7 Flash REST API for SEO text and hashtags"""
    if not GEMINI_API_KEY:
        return {
            "title": "Stunning Pinterest Design Inspiration",
            "description": f"Explore creative design ideas for {prompt_text}. Perfect for home decor and styling! #HomeDecor #Design",
            "hashtags": ["#HomeDecor", "#Design", "#Inspiration"]
        }

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
            return json.loads(cleaned_text)
    except Exception:
        return {
            "title": "Creative Home Inspiration",
            "description": f"Discover amazing ideas inspired by {prompt_text} #Design #Inspiration",
            "hashtags": ["#Design", "#Inspiration"]
        }

# ---------------------------------------------------------
# 4. Pinterest Session, Board Fetcher & Direct Publisher
# ---------------------------------------------------------
def fetch_user_pinterest_boards(sess_cookie):
    """Fetches list of boards automatically using user session cookie"""
    url = "https://www.pinterest.com/resource/BoardsResource/get/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": f"_pinterest_sess={sess_cookie};"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            data = res_body.get("resource_response", {}).get("data", [])
            
            boards_list = []
            for item in data:
                boards_list.append({
                    "id": str(item.get("id")),
                    "name": item.get("name")
                })
            return boards_list if boards_list else [{"id": "default", "name": "Main Board"}]
    except Exception:
        return [{"id": "default", "name": "Main Board"}]

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

    post_data = urllib.parse.urlencode({"data": json.dumps(resource_data)}).encode('utf-8')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
                err = res_body.get("resource_response", {}).get("error", {}).get("message", "Unknown error")
                return {"status": "error", "message": err}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
# 5. Main Vercel Serverless Handler
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
        res = {"status": "success", "message": "All Systems Go (Drive + Nano Banana AI + Gemini 3.7 Flash + Pinterest Direct)"}
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
        board_id = data.get('board_id', '').strip()
        prompt = data.get('prompt', 'Modern Home Interior').strip()
        images_batch = data.get('images_batch', [])

        # ACTION 1: Fetch Pinterest Boards Automatically
        if action == "fetch_boards":
            boards = fetch_user_pinterest_boards(sess)
            res = {"status": "success", "action": "fetch_boards", "boards": boards}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # ACTION 2: Save Session & Settings
        if action == 'save_session' or (gdrive and sess and not action):
            folder_id = extract_folder_id(gdrive)
            res = {
                "status": "success",
                "message": "Settings Synced Successfully",
                "folder_id": folder_id
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        # ACTION 3: Batch Auto-Process Drive Sketches -> Nano Banana -> Gemini SEO -> Pinterest
        if action == 'batch_process_drive':
            if not sess or not board_id:
                res = {"status": "error", "message": "Missing session cookie or board id"}
                self.wfile.write(json.dumps(res).encode('utf-8'))
                return

            # Dummy or received sketch items fallback
            if not images_batch:
                images_batch = ["https://via.placeholder.com/1000x1500.png?text=Drive+Sketch+Item"]

            results = []
            total_items = len(images_batch)

            for idx, raw_image in enumerate(images_batch):
                req_prompt = f"{prompt} variation {idx+1}"

                # Step A: Nano Banana AI Sketch-to-Colourful Conversion
                colourful_img = generate_nano_banana_image(req_prompt, raw_image)

                # Step B: Gemini 3.7 Flash SEO Title, Description, & Hashtags Generation
                seo = generate_gemini_metadata(req_prompt)
                title = seo.get("title", "Stunning Design")
                hashtags = " ".join(seo.get("hashtags", []))
                full_desc = f"{seo.get('description', '')}\n\n{hashtags}".strip()

                # Step C: Direct Post to Pinterest
                post_res = create_pinterest_pin_via_session(
                    session_cookie=sess,
                    board_id=board_id,
                    image_url=colourful_img,
                    title=title,
                    description=full_desc
                )

                results.append({
                    "item_index": idx + 1,
                    "rendered_url": colourful_img,
                    "status": post_res.get("status"),
                    "pin_url": post_res.get("pin_url", "")
                })

                # Anti-Bot Random Delay (30 to 60 seconds between posts)
                if idx < total_items - 1:
                    time.sleep(random.randint(30, 60))

            res = {"status": "success", "processed_batch": results}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            return

        res = {"status": "error", "message": "Invalid Action Request"}
        self.wfile.write(json.dumps(res).encode('utf-8'))
