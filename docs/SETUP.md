# Setup checklist

1. Create a Vercel Blob store and copy its read/write token into `BLOB_READ_WRITE_TOKEN`.
2. Create a Gemini API key and put it in `GEMINI_API_KEY`.
3. Create/approve the Pinterest developer app. Pinterest's current docs require a business account for API access. Add the exact Vercel callback URI.
4. Add Pinterest client ID/secret.
5. Set `PINTEREST_REDIRECT_URI` to `https://YOUR-DOMAIN/api/pinterest/callback`.
6. Set `ADMIN_PASSWORD`.
7. Generate a random `APP_ENCRYPTION_KEY`.
8. Set `CRON_SECRET`.
9. Optionally create a Google Drive API key. If you don't, the app uses a best-effort public folder scanner.
10. Deploy.
11. Login to the dashboard.
12. Add a student and a public/shared Drive folder.
13. Connect that student's Pinterest.
14. Load the first board.
15. Click Generate Next Pin.
16. Review the image + SEO in Approval Queue.
17. Approve & Publish.
18. After several successful tests, switch the student to Auto.

AI disclosure: Pinterest's Create Pin API supports an `ai_disclosures` field; this project marks generated Pins as `AI_MODIFIED`.
