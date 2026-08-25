# PinPilot AI — Pinterest AI Agent

A Vercel-ready Next.js starter for an AI Pinterest automation platform.

## Current phase

This starter includes:

- Next.js App Router
- Professional dashboard shell
- Human Approval / Fully Automatic mode UI
- Server-only Gemini API integration
- Gemini connection test endpoint
- Pinterest OAuth redirect skeleton
- Pinterest OAuth callback skeleton
- Vercel Cron endpoint
- `.env.example`
- Vercel deployment configuration

The production database, encrypted token storage, Google Drive resolver, image-generation worker, approval queue persistence, and Pinterest publishing worker are intentionally the next phase.

## Requirements

- Node.js 20.9+
- npm / pnpm
- Vercel account
- Gemini API key
- Pinterest developer app

## Environment variables

Copy `.env.example` to `.env.local` for local development.

Important:

`GEMINI_API_KEY` is server-only. Do not use `NEXT_PUBLIC_GEMINI_API_KEY`.

For Vercel, add the variables in Project → Settings → Environment Variables.

## Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Deploy

Push this repository to GitHub and import it into Vercel.

Vercel will detect Next.js automatically.

## Pinterest OAuth

Register the exact redirect URI:

`https://YOUR-DOMAIN/api/pinterest/callback`

For local testing:

`http://localhost:3000/api/pinterest/callback`

The final implementation must persist and validate OAuth `state` per signed-in user before exchanging the authorization code.

## Scheduler

`vercel.json` currently schedules `/api/cron` once daily at 20:00 UTC.

Vercel Hobby cron scheduling is daily with hourly timing precision. For user-selected exact posting times and frequent schedules, use a Pro plan or move scheduling to a dedicated queue/worker.

## AI models

Text analysis currently uses `gemini-2.5-flash`.

The image-generation constant is set to `gemini-3.1-flash-image` (Nano Banana 2) based on the current Gemini API model documentation. The image worker will be implemented next.
