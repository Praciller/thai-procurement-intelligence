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
- `NEXT_PUBLIC_SITE_URL` (use the public production alias, for example `https://thai-procurement-intelligence.vercel.app`)
- `NEXT_PUBLIC_DEMO_MODE`

The root `vercel.json` defines two services:

- `web`: `apps/web` at `/`
- `api`: `apps/api/main.py` at `/backend`

Because Vercel strips the service prefix before forwarding to FastAPI, browser requests should use `/backend/api`.
The FastAPI service targets Python 3.12 because the Vercel Services Python runtime requires it.
Server-rendered Next.js pages also need `NEXT_PUBLIC_SITE_URL`; otherwise a relative API base can resolve through a protected deployment URL and produce fallback zero-data pages.

Operational checks:

- Liveness: `/backend/api/health`
- Readiness with database count: `/backend/api/health/readiness`
- Data count smoke: `/backend/api/records?page_size=1`

CI runs on every push and pull request through `.github/workflows/ci.yml`:

- `uv run pytest`
- `npm run web:test`
- `npm run web:lint`
- `npm run web:build`

Run ingestion after deployment:

```bash
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```
