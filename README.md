# AI Pinterest Agent — single-file Vercel testing build

This build intentionally keeps the backend in one `app.py` so it is easy to inspect, upload to GitHub, and deploy to Vercel.

## Architecture

Google Drive -> Gemini image transformation + SEO -> Pinterest API v5

Each student connects:
1. Their own Google account/Drive folder through Google OAuth.
2. Their own normal Pinterest account through Pinterest OAuth.
3. Their Pinterest board (optional; if omitted, first available board is used).

One academy-owned Pinterest developer app can authorize multiple independent users. Students do not create developer apps.

## Important

This uses official OAuth and Pinterest API v5. It does NOT read `_pinterest_sess`, CSRF cookies, passwords, or private Pinterest endpoints.

Pinterest requires a registered/approved developer app for API access. Its documentation states Authorization Code is intended for web apps serving multiple independent end users.

## Vercel Hobby cron

The included `vercel.json` contains exactly ONE daily cron:
`0 3 * * *`

Current Vercel documentation says Hobby cron is once per day per cron job. Therefore this build processes at most one queued item from the cron invocation. Upgrade later if you need more frequent processing. Do not change the Hobby cron to hourly/minutely.

## Database

SQLite works for local testing only. Vercel filesystem is not durable across invocations, so production must use persistent Postgres.

Set `DATABASE_URL` to a managed Postgres database.

## Secrets

Never commit `.env`, API keys, OAuth secrets, refresh tokens, or `FERNET_KEY`.

## Local test

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
python app.py
```

Open http://127.0.0.1:5000

For local Google/Pinterest OAuth, register:
- http://127.0.0.1:5000/oauth/google/callback
- http://127.0.0.1:5000/oauth/pinterest/callback

## Vercel

1. Push the files to GitHub.
2. Import the repo into Vercel.
3. Add all variables from `.env.example`.
4. Use a persistent Postgres database.
5. Update Google OAuth redirect URI to your exact Vercel URL.
6. Update Pinterest OAuth redirect URI to your exact Vercel URL.
7. Deploy.
8. Test with ONE image first.

## Google Drive

The app expects a folder URL or folder ID. It lists direct child image files only.

## Pinterest

Required OAuth scopes:
- boards:read
- boards:write
- pins:read
- pins:write
- user_accounts:read

The Create Pin endpoint is `/v5/pins`.

## Job behavior

`/api/drive/scan` creates one queue record per Drive file ID, preventing duplicate processing.

`/api/automation/process-one` processes one queued job for the signed-in user.

`/api/cron/process-one` processes one queued job globally and is protected by `X-Cron-Secret`.

## Production weaknesses still to address before a large student rollout

- Add a real queue/worker for frequent processing.
- Add object storage for generated images instead of storing Base64 in the DB.
- Add per-user quotas and admin controls.
- Add CSRF protection to all state-changing dashboard forms.
- Add stronger rate limiting and audit logs.
- Add database migrations (Alembic).
- Add a privacy policy and terms page before public OAuth app review.
- Add Pinterest app review/standard access as required by Pinterest.
- Add retry/backoff with idempotency for transient API failures.
- Add monitoring/error reporting.

This is intentionally an MVP testing build, not a claim that third-party OAuth/API approval or quotas can be bypassed.
