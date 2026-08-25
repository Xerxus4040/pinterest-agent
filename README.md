# PinPilot AI — Final Vercel Project

This version is a real working foundation, not a static dashboard.

## What works

- Admin login
- Add students
- Save public Google Drive folder URLs
- Scan a public Drive folder (Drive API if GOOGLE_DRIVE_API_KEY is supplied; otherwise best-effort public-folder scan)
- Pinterest OAuth 2.0 connection
- Fetch Pinterest boards
- Select a board (first board button; can be expanded in UI)
- Gemini blueprint analysis
- Gemini SEO title/description/tags/alt text
- Nano Banana 2 (`gemini-3.1-flash-image`) image generation from the source blueprint
- Store generated images in Vercel Blob
- Human approval queue
- Approve & publish to Pinterest
- Auto mode
- Server-side scheduler endpoint
- Persistent application state in Vercel Blob
- Encrypted Pinterest access/refresh tokens

## Required Vercel environment variables

Create a Vercel Blob store and add:

- `BLOB_READ_WRITE_TOKEN`
- `GEMINI_API_KEY`
- `PINTEREST_CLIENT_ID`
- `PINTEREST_CLIENT_SECRET`
- `PINTEREST_REDIRECT_URI`
- `ADMIN_PASSWORD`
- `APP_ENCRYPTION_KEY`
- `CRON_SECRET`

Optional:

- `GOOGLE_DRIVE_API_KEY`

Use a long random value for `APP_ENCRYPTION_KEY`.

## Pinterest app

Pinterest requires the app administrator to use a Pinterest business account and the app must be approved for API access. Configure the exact redirect URI in the Pinterest app:

`https://YOUR-VERCEL-DOMAIN/api/pinterest/callback`

The application requests:
`boards:read boards:write pins:read pins:write user_accounts:read`

## Important

A Pinterest access token is not a normal "API key". The app uses OAuth so each student's Pinterest account authorizes the app.

## Google Drive

The most reliable method is to provide `GOOGLE_DRIVE_API_KEY` and share the folder so its contents are readable. The code also attempts a public-folder HTML scan when no Drive API key is supplied, but Google can change its HTML and this is inherently less reliable.

## Scheduler

The included cron runs hourly and checks each student's local hour. This avoids creating a cron per student. Exact minute-level scheduling may require a Vercel plan that supports the needed cron frequency.

## Production note

For a larger SaaS, move state from Blob JSON to a real database and use a durable queue/workflow system. This Blob-backed version is intentionally optimized for a small academy deployment and minimal setup.

## Local

```bash
npm install
npm run dev
```

## Deploy

Push the project to GitHub and import it into Vercel. Add the environment variables before deploying.
