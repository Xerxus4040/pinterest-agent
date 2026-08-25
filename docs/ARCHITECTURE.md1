# Production Architecture

## User flow

1. Admin creates/activates a student.
2. Student adds a Google Drive folder URL.
3. Student connects Pinterest through OAuth.
4. Student chooses board, schedule, frequency and creative settings.
5. Agent scans the source folder.
6. AI analyzes each blueprint.
7. AI generates a marketing brief.
8. Nano Banana generates a Pinterest creative.
9. SEO agent generates title/description/keywords.
10. QA checks image and metadata.
11. Human Approval mode: item enters approval queue.
12. Fully Automatic mode: approved-by-policy item enters publish queue.
13. Pinterest worker creates the Pin.
14. Result is logged.

## Data model (planned)

- users
- pinterest_accounts
- drive_sources
- boards
- automation_settings
- source_assets
- ai_jobs
- generated_creatives
- approval_items
- publish_jobs
- published_pins
- activity_logs

## Security

- Gemini key stays server-side.
- Pinterest client secret stays server-side.
- OAuth access/refresh tokens are encrypted at rest.
- OAuth state is generated per connection attempt and validated.
- Cron endpoint is protected with CRON_SECRET.
- User authorization must be checked on every resource/action.

## Queue

Use durable jobs rather than making a single request perform:
Drive download -> AI -> image generation -> Pinterest.

Each stage should be retryable and idempotent.

## Scheduling

Store each user's timezone and schedule in the database. A scheduler should find due jobs and enqueue them. Do not create one Vercel cron per student.

## Pinterest

Use official Pinterest OAuth authorization code flow for multi-user access. Request only required scopes:
boards:read boards:write pins:read pins:write.

Publishing uses the official Pins API.
