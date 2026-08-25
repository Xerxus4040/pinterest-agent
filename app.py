
import os, re, json, base64, secrets, hashlib, mimetypes, logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import requests
from flask import Flask, request, session, redirect, jsonify, render_template_string
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from cryptography.fernet import Fernet
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ai-pinterest-agent")

APP = Flask(__name__)
APP.secret_key = os.environ.get("APP_SECRET", "dev-only-change-me")
APP.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
DB = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

FERNET_KEY = os.environ.get("FERNET_KEY")
if FERNET_KEY:
    fernet = Fernet(FERNET_KEY.encode())
else:
    fernet = None

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI")
PINTEREST_CLIENT_ID = os.environ.get("PINTEREST_CLIENT_ID")
PINTEREST_CLIENT_SECRET = os.environ.get("PINTEREST_CLIENT_SECRET")
PINTEREST_REDIRECT_URI = os.environ.get("PINTEREST_REDIRECT_URI")
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_TEXT_MODEL = os.environ.get("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
CRON_SECRET = os.environ.get("CRON_SECRET", "")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Connection(Base):
    __tablename__ = "connections"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    provider = Column(String(30), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    extra = Column(Text, default="{}")
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    drive_file_id = Column(String(255), nullable=False)
    drive_file_name = Column(String(500))
    board_id = Column(String(255))
    status = Column(String(40), default="queued")
    title = Column(String(100))
    description = Column(Text)
    hashtags = Column(Text)
    generated_image_b64 = Column(Text)
    pinterest_pin_id = Column(String(255))
    error = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("user_id", "drive_file_id", name="uq_user_file"),)

Base.metadata.create_all(engine)

# Vercel Python runtime entrypoint: it looks for a top-level variable named `app`.
app = APP

INDEX_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Pinterest Agent</title>
<style>
body{font-family:Inter,system-ui;background:#f5f6f8;margin:0;color:#171717}.wrap{max-width:1050px;margin:40px auto;padding:0 18px}
.card{background:#fff;border:1px solid #ddd;border-radius:16px;padding:22px;margin:16px 0;box-shadow:0 5px 20px #00000008}
button{border:0;border-radius:10px;padding:11px 15px;background:#111;color:white;cursor:pointer;margin:4px}
button.secondary{background:#eee;color:#111}input,select{width:100%;box-sizing:border-box;padding:12px;border:1px solid #ccc;border-radius:10px;margin:7px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}.pill{display:inline-block;padding:6px 10px;border-radius:999px;background:#eee}
pre{white-space:pre-wrap;overflow:auto;background:#111;color:#eee;padding:12px;border-radius:10px}.muted{color:#666}
</style></head>
<body><div class="wrap">
<h1>AI Pinterest Agent</h1>
<p class="muted">Drive → Gemini → SEO → Pinterest</p>
<div class="card">
{% if email %}<b>Signed in:</b> {{email}}{% else %}<b>Not signed in</b>{% endif %}
<div style="margin-top:12px">
<a href="/auth/google"><button>Connect Google Drive</button></a>
<a href="/auth/pinterest"><button>Connect Pinterest</button></a>
</div>
</div>
<div class="grid">
<div class="card"><h3>Connections</h3><div>Google: <span class="pill">{{google}}</span></div><div>Pinterest: <span class="pill">{{pinterest}}</span></div></div>
<div class="card"><h3>Automation</h3><form method="post" action="/api/drive/scan"><button>Scan Drive</button></form><form method="post" action="/api/automation/process-one"><button>Process One</button></form><p class="muted">Cron endpoint processes one queued item per invocation.</p></div>
</div>
<div class="card">
<h3>Google Drive folder</h3>
<form method="post" action="/api/settings">
<input name="folder_url" placeholder="Paste Google Drive folder URL or folder ID" value="{{folder_url}}">
<input name="board_id" placeholder="Pinterest board ID (optional)" value="{{board_id}}">
<button>Save settings</button>
</form>
</div>
<div class="card"><h3>Recent jobs</h3>
{% for j in jobs %}<div style="border-top:1px solid #eee;padding:12px 0"><b>#{{j.id}} {{j.drive_file_name}}</b> — {{j.status}}{% if j.pinterest_pin_id %} — Pin {{j.pinterest_pin_id}}{% endif %}{% if j.error %}<pre>{{j.error}}</pre>{% endif %}</div>{% else %}<p class="muted">No jobs yet.</p>{% endfor %}
</div>
<div class="card"><h3>API health</h3><pre>{{health}}</pre></div>
</div></body></html>
"""

def enc(value):
    if not value: return None
    if not fernet:
        return value
    return fernet.encrypt(value.encode()).decode()

def dec(value):
    if not value: return None
    if not fernet:
        return value
    return fernet.decrypt(value.encode()).decode()

def current_user(db):
    uid = session.get("user_id")
    return db.get(User, uid) if uid else None

def require_user():
    if not session.get("user_id"):
        return redirect("/")
    return None

def json_error(message, status=400, detail=None):
    payload={"status":"error","message":message}
    if detail is not None: payload["detail"]=detail
    return jsonify(payload), status

def oauth_state(prefix):
    raw = secrets.token_urlsafe(32)
    session[f"oauth_state_{prefix}"] = raw
    return raw

def parse_folder_id(value):
    if not value: return None
    value=value.strip()
    m=re.search(r"/folders/([A-Za-z0-9_-]+)", value)
    return m.group(1) if m else value

def google_token(conn, db):
    token=dec(conn.access_token)
    exp=conn.expires_at
    if exp and exp > datetime.now(timezone.utc)+timedelta(minutes=2):
        return token
    if not conn.refresh_token:
        return token
    refresh=dec(conn.refresh_token)
    r=requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":GOOGLE_CLIENT_ID,"client_secret":GOOGLE_CLIENT_SECRET,
        "refresh_token":refresh,"grant_type":"refresh_token"
    },timeout=20)
    if not r.ok: raise RuntimeError(f"Google token refresh failed: {r.status_code} {r.text}")
    data=r.json()
    conn.access_token=enc(data["access_token"])
    conn.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(data.get("expires_in",3600)))
    db.commit()
    return data["access_token"]

def pinterest_token(conn, db):
    token=dec(conn.access_token)
    exp=conn.expires_at
    if exp and exp > datetime.now(timezone.utc)+timedelta(minutes=2):
        return token
    refresh=dec(conn.refresh_token) if conn.refresh_token else None
    if not refresh: return token
    basic=base64.b64encode(f"{PINTEREST_CLIENT_ID}:{PINTEREST_CLIENT_SECRET}".encode()).decode()
    r=requests.post("https://api.pinterest.com/v5/oauth/token",
        headers={"Authorization":f"Basic {basic}","Content-Type":"application/x-www-form-urlencoded"},
        data={"grant_type":"refresh_token","refresh_token":refresh,"continuous_refresh":"true"},
        timeout=20)
    if not r.ok: raise RuntimeError(f"Pinterest token refresh failed: {r.status_code} {r.text}")
    data=r.json()
    conn.access_token=enc(data["access_token"])
    if data.get("refresh_token"): conn.refresh_token=enc(data["refresh_token"])
    conn.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(data.get("expires_in",2592000)))
    db.commit()
    return data["access_token"]

def drive_list_images(token, folder_id):
    headers={"Authorization":f"Bearer {token}"}
    q=f"'{folder_id}' in parents and trashed=false and mimeType contains 'image/'"
    r=requests.get("https://www.googleapis.com/drive/v3/files",headers=headers,
        params={"q":q,"pageSize":100,"fields":"files(id,name,mimeType,modifiedTime,webContentLink)"},
        timeout=30)
    if not r.ok: raise RuntimeError(f"Google Drive list failed: {r.status_code} {r.text}")
    return r.json().get("files",[])

def drive_download(token,file_id):
    r=requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization":f"Bearer {token}"},
        params={"alt":"media"},timeout=60)
    if not r.ok: raise RuntimeError(f"Google Drive download failed: {r.status_code} {r.text[:1000]}")
    return r.content, r.headers.get("Content-Type","image/png")

def ai_generate(image_bytes,mime_type,style="premium colorful Pinterest presentation"):
    if not GEMINI_API_KEY: raise RuntimeError("GEMINI_API_KEY is missing.")
    client=genai.Client(api_key=GEMINI_API_KEY)
    prompt=f"""Transform this user-provided sketch/blueprint into a polished original Pinterest-ready visual.
Preserve the core concept and important geometry/content of the source, but improve presentation, color, lighting,
composition and visual appeal. Do not add logos, trademarks, misleading claims, or unrelated objects.
Style: {style}. Vertical Pinterest composition, 2:3 aspect ratio, clean premium Etsy-inspired presentation."""
    response=client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes,mime_type=mime_type)
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            response_format={"image":{"aspect_ratio":"2:3","image_size":"1K"}}
        )
    )
    for part in response.parts:
        if getattr(part,"inline_data",None):
            return base64.b64encode(part.inline_data.data).decode(), part.inline_data.mime_type or "image/png"
    raise RuntimeError("Gemini returned no image.")

def ai_seo(file_name):
    if not GEMINI_API_KEY: raise RuntimeError("GEMINI_API_KEY is missing.")
    client=genai.Client(api_key=GEMINI_API_KEY)
    prompt=f"""Create Pinterest SEO metadata for a design/sketch asset named "{file_name}".
Return ONLY valid JSON:
{{"title":"max 100 chars","description":"useful engaging description with a natural CTA, max 800 chars","hashtags":["#tag1","#tag2","#tag3","#tag4","#tag5"],"alt_text":"descriptive accessibility text"}}
Do not invent factual claims about products. Avoid spammy keyword stuffing."""
    r=client.models.generate_content(
        model=GEMINI_TEXT_MODEL,contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    data=json.loads(r.text)
    data["title"]=str(data.get("title",""))[:100]
    data["description"]=str(data.get("description",""))[:800]
    data["hashtags"]=[str(x) for x in data.get("hashtags",[])][:12]
    return data

def pinterest_get_boards(token):
    r=requests.get("https://api.pinterest.com/v5/boards",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        params={"page_size":100},timeout=20)
    if not r.ok: raise RuntimeError(f"Pinterest boards failed: {r.status_code} {r.text}")
    return r.json().get("items",[])

def pinterest_create_pin(token,board_id,image_b64,mime,title,description,alt_text=None,link=None):
    body={
        "board_id":str(board_id),
        "title":title[:100],
        "description":description[:800],
        "alt_text":(alt_text or "")[:500],
        "media_source":{"source_type":"image_base64","content_type":mime,"data":image_b64}
    }
    if link: body["link"]=link
    r=requests.post("https://api.pinterest.com/v5/pins",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        json=body,timeout=60)
    if not r.ok:
        msg={401:"Pinterest authorization expired/invalid.",403:"Pinterest denied this operation.",400:"Pinterest rejected the Pin payload."}.get(r.status_code,"Pinterest API error.")
        raise RuntimeError(f"{msg} HTTP {r.status_code}: {r.text}")
    return r.json()

@APP.get("/")
def index():
    db=DB()
    u=current_user(db)
    google=bool(u and db.query(Connection).filter_by(user_id=u.id,provider="google").first())
    pinterest=bool(u and db.query(Connection).filter_by(user_id=u.id,provider="pinterest").first())
    settings= json.loads((db.query(Connection).filter_by(user_id=u.id,provider="settings").first().extra if u else "{}") or "{}")
    jobs=db.query(Job).filter_by(user_id=u.id).order_by(Job.id.desc()).limit(20).all() if u else []
    health={"backend":"ok","gemini_configured":bool(GEMINI_API_KEY),"database":DATABASE_URL.split(":")[0],"time":datetime.now(timezone.utc).isoformat()}
    return render_template_string(INDEX_HTML,email=u.email if u else None,google="Connected" if google else "Not connected",
        pinterest="Connected" if pinterest else "Not connected",folder_url=settings.get("folder_url",""),
        board_id=settings.get("board_id",""),jobs=jobs,health=json.dumps(health,indent=2))

@APP.get("/auth/google")
def auth_google():
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI: return "Google OAuth is not configured.",500
    state=oauth_state("google")
    params={"client_id":GOOGLE_CLIENT_ID,"redirect_uri":GOOGLE_REDIRECT_URI,"response_type":"code",
            "scope":"openid email https://www.googleapis.com/auth/drive.readonly","access_type":"offline","prompt":"consent","state":state}
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?"+urlencode(params))

@APP.get("/oauth/google/callback")
def google_callback():
    if request.args.get("state") != session.pop("oauth_state_google",None): return "Invalid OAuth state.",400
    code=request.args.get("code")
    r=requests.post("https://oauth2.googleapis.com/token",data={
        "code":code,"client_id":GOOGLE_CLIENT_ID,"client_secret":GOOGLE_CLIENT_SECRET,
        "redirect_uri":GOOGLE_REDIRECT_URI,"grant_type":"authorization_code"},timeout=20)
    if not r.ok:return f"Google token exchange failed: {r.text}",400
    data=r.json()
    info=requests.get("https://openidconnect.googleapis.com/v1/userinfo",headers={"Authorization":f"Bearer {data['access_token']}"},timeout=20)
    if not info.ok:return f"Google userinfo failed: {info.text}",400
    email=info.json().get("email")
    db=DB(); u=db.query(User).filter_by(email=email).first()
    if not u:u=User(email=email);db.add(u);db.flush()
    c=db.query(Connection).filter_by(user_id=u.id,provider="google").first()
    if not c:c=Connection(user_id=u.id,provider="google");db.add(c)
    c.access_token=enc(data["access_token"]);c.refresh_token=enc(data.get("refresh_token"));c.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(data.get("expires_in",3600)))
    db.commit();session["user_id"]=u.id
    return redirect("/")

@APP.get("/auth/pinterest")
def auth_pinterest():
    if not session.get("user_id"): return redirect("/auth/google")
    if not PINTEREST_CLIENT_ID or not PINTEREST_REDIRECT_URI:return "Pinterest OAuth is not configured.",500
    state=oauth_state("pinterest")
    scopes="boards:read boards:write pins:read pins:write user_accounts:read"
    params={"response_type":"code","client_id":PINTEREST_CLIENT_ID,"redirect_uri":PINTEREST_REDIRECT_URI,
            "scope":scopes,"state":state}
    return redirect("https://www.pinterest.com/oauth/?"+urlencode(params))

@APP.get("/oauth/pinterest/callback")
def pinterest_callback():
    if request.args.get("state") != session.pop("oauth_state_pinterest",None): return "Invalid OAuth state.",400
    code=request.args.get("code")
    basic=base64.b64encode(f"{PINTEREST_CLIENT_ID}:{PINTEREST_CLIENT_SECRET}".encode()).decode()
    r=requests.post("https://api.pinterest.com/v5/oauth/token",
        headers={"Authorization":f"Basic {basic}","Content-Type":"application/x-www-form-urlencoded"},
        data={"grant_type":"authorization_code","code":code,"redirect_uri":PINTEREST_REDIRECT_URI,"continuous_refresh":"true"},timeout=20)
    if not r.ok:return f"Pinterest token exchange failed: {r.text}",400
    data=r.json(); db=DB();uid=session["user_id"]
    c=db.query(Connection).filter_by(user_id=uid,provider="pinterest").first()
    if not c:c=Connection(user_id=uid,provider="pinterest");db.add(c)
    c.access_token=enc(data["access_token"]);c.refresh_token=enc(data.get("refresh_token"));c.expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(data.get("expires_in",2592000)))
    db.commit();return redirect("/")

@APP.post("/api/settings")
def settings():
    if not session.get("user_id"): return redirect("/auth/google")
    db=DB(); c=db.query(Connection).filter_by(user_id=session["user_id"],provider="settings").first()
    if not c:c=Connection(user_id=session["user_id"],provider="settings",access_token="");db.add(c)
    c.extra=json.dumps({"folder_url":request.form.get("folder_url","").strip(),"board_id":request.form.get("board_id","").strip()})
    db.commit();return redirect("/")

@APP.post("/api/drive/scan")
def scan():
    if not session.get("user_id"):return json_error("Login with Google first.",401)
    db=DB();u=current_user(db)
    gc=db.query(Connection).filter_by(user_id=u.id,provider="google").first()
    sc=db.query(Connection).filter_by(user_id=u.id,provider="settings").first()
    if not gc or not sc:return json_error("Connect Google Drive and save a folder first.",400)
    settings=json.loads(sc.extra or "{}");folder=parse_folder_id(settings.get("folder_url"))
    if not folder:return json_error("Google Drive folder URL/ID is missing.",400)
    try:files=drive_list_images(google_token(gc,db),folder)
    except Exception as e:return json_error("Drive scan failed.",502,str(e))
    added=0
    for f in files:
        if not db.query(Job).filter_by(user_id=u.id,drive_file_id=f["id"]).first():
            db.add(Job(user_id=u.id,drive_file_id=f["id"],drive_file_name=f["name"],status="queued"));added+=1
    db.commit();return jsonify({"status":"ok","found":len(files),"queued":added})

@APP.get("/api/boards")
def boards():
    if not session.get("user_id"):return json_error("Login first.",401)
    db=DB();c=db.query(Connection).filter_by(user_id=session["user_id"],provider="pinterest").first()
    if not c:return json_error("Connect Pinterest first.",400)
    try:return jsonify({"status":"ok","boards":pinterest_get_boards(pinterest_token(c,db))})
    except Exception as e:return json_error("Could not fetch Pinterest boards.",502,str(e))

@APP.post("/api/automation/process-one")
def process_one():
    if CRON_SECRET and request.headers.get("X-Cron-Secret") != CRON_SECRET and not session.get("user_id"):
        return json_error("Unauthorized.",401)
    db=DB()
    uid=session.get("user_id")
    q=db.query(Job).filter_by(status="queued")
    if uid:q=q.filter_by(user_id=uid)
    job=q.order_by(Job.id.asc()).first()
    if not job:return jsonify({"status":"idle","message":"No queued jobs."})
    job.status="processing";job.updated_at=datetime.now(timezone.utc);db.commit()
    try:
        gc=db.query(Connection).filter_by(user_id=job.user_id,provider="google").first()
        pc=db.query(Connection).filter_by(user_id=job.user_id,provider="pinterest").first()
        sc=db.query(Connection).filter_by(user_id=job.user_id,provider="settings").first()
        if not gc or not pc: raise RuntimeError("Google Drive or Pinterest is not connected.")
        settings=json.loads(sc.extra or "{}") if sc else {}
        board_id=settings.get("board_id")
        token=google_token(gc,db)
        image,mime=drive_download(token,job.drive_file_id)
        seo=ai_seo(job.drive_file_name)
        generated_b64,generated_mime=ai_generate(image,mime)
        if not board_id:
            boards=pinterest_get_boards(pinterest_token(pc,db))
            if not boards: raise RuntimeError("No Pinterest boards available.")
            board_id=boards[0]["id"]
        result=pinterest_create_pin(pinterest_token(pc,db),board_id,generated_b64,generated_mime,seo["title"],seo["description"],seo.get("alt_text"))
        job.board_id=board_id;job.title=seo["title"];job.description=seo["description"];job.hashtags=json.dumps(seo.get("hashtags",[]))
        job.generated_image_b64=generated_b64;job.pinterest_pin_id=str(result.get("id",""));job.status="published";job.error=None
        db.commit()
        return jsonify({"status":"published","action":"publish_pin","prompt":"Transform sketch into a premium colorful Pinterest visual.","generated_image":"data:"+generated_mime+";base64,"+generated_b64,"seo":seo,"pinterest_post_result":result})
    except Exception as e:
        log.exception("job failed")
        job.status="failed";job.error=str(e);job.updated_at=datetime.now(timezone.utc);db.commit()
        return json_error("Job failed.",502,str(e))

@APP.get("/api/health")
def health():
    return jsonify({"status":"ok","gemini_configured":bool(GEMINI_API_KEY),"database":DATABASE_URL.split(":")[0]})

@APP.post("/api/cron/process-one")
def cron():
    if CRON_SECRET and not secrets.compare_digest(request.headers.get("X-Cron-Secret",""),CRON_SECRET):
        return json_error("Unauthorized.",401)
    return process_one()

@APP.get("/logout")
def logout():
    session.clear();return redirect("/")

if __name__ == "__main__":
    APP.run(host="0.0.0.0",port=int(os.environ.get("PORT","5000")),debug=True)
