# Deployment

Recommended free-tier path:

1. Supabase PostgreSQL for `DATABASE_URL`.
2. Vercel Services for both `apps/web` and `apps/api`.
3. Optional Cloudflare DNS only when using a custom domain.

Backend environment:

- `DATABASE_URL`
- `LLM_PROVIDER`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `ENABLE_LLM`
- `ENABLE_EMBEDDINGS`
- `AI_RATE_LIMIT_PER_HOUR`
- `CORS_ORIGINS`

Frontend environment:

- `NEXT_PUBLIC_API_BASE_URL` (use `/backend/api` on Vercel Services)
- `NEXT_PUBLIC_DEMO_MODE`

The root `vercel.json` defines two services:

- `web`: `apps/web` at `/`
- `api`: `apps/api/main.py` at `/backend`

Because Vercel strips the service prefix before forwarding to FastAPI, browser requests should use `/backend/api`.
The FastAPI service targets Python 3.12 because the Vercel Services Python runtime requires it.

Run ingestion after deployment:

```bash
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```
