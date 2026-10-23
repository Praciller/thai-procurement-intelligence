# Security and secret rotation

Do not commit credentials, database URLs, or access tokens.

Runtime secrets belong in deployment environment variables. If any credential is pasted into chat, terminal logs, screenshots, issue text, or public Git history, treat it as exposed and rotate it at the issuing service.

## Rotation checklist

1. Revoke the exposed credential.
2. Create a replacement with the smallest scope needed.
3. Update the protected runtime environment variable.
4. Redeploy the affected service.
5. Run production smoke checks:

```bash
curl https://thai-procurement-intelligence.vercel.app/backend/api/health
curl https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness
curl "https://thai-procurement-intelligence.vercel.app/backend/api/records?page_size=1"
```

## Public client variables

These are intentionally public because browser code can read any `NEXT_PUBLIC_` value:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SITE_URL`

Never put private credentials in `NEXT_PUBLIC_` variables.

## Inference boundary

The public summary and cited-answer paths are deterministic and require no external inference credential. Results remain bounded by stored and retrieved procurement records and must be reviewed against source evidence.

## Data ingestion and export

- Public ingestion and the database-writing `POST /api/records/{id}/embedding` endpoint are disabled unless a server-side `ADMIN_INGESTION_TOKEN` is configured and supplied as the `X-Admin-Token` request header. Read-only search and mock assistant behavior do not require this token.
- Uploads accept CSV content types only, stop above 2 MB, and delete temporary files after processing.
- Automated acquisition is hard-coded to the approved `data.go.th` HTTPS URL, uses a timeout and 1 MiB response limit, validates content type, and verifies SHA-256 before import.
- The public API does not accept arbitrary acquisition URLs or filesystem paths.
- CSV export prefixes cells beginning with `=`, `+`, `-`, or `@` to prevent spreadsheet formula execution.
- React escapes displayed source text.

## Assistant input and optional inference limits

- External-capable LLM paths validate the assembled system/user prompt, including retrieved record context, before reserving the shared hourly budget. Payloads exceeding 24,000 characters return HTTP 413 and do not contact external providers. This cap also protects mock-first chains that might fall back externally; offline-only mock responses are unaffected.
- The Assistant accepts only typed, documented filters (`province`, `agency`, `category`, `method`, `min_budget`, `max_budget`, `date_from`, `date_to`); invalid types, unknown keys, reversed ranges, and malformed dates return HTTP 422. The global hourly budget is not per-user throttling. Leave external LLMs disabled until abuse controls and deployment threat modeling are reviewed.

## Ethics

Public records are not proof of wrongdoing. Agency or vendor names must not be ranked as suspicious without a separately validated methodology. Generated summaries require review against official records. The snapshot may be incomplete or stale, and procurement decisions require verification at the official source.
