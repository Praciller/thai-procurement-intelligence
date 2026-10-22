# Deployment

Deployment is optional. The primary review path is [local_review.md](local_review.md) and requires no hosted inference account or inference credential.

Current optional hosted path:

1. Supabase PostgreSQL for `DATABASE_URL`.
2. Vercel Services for both `apps/web` and `apps/api`.
3. Optional Cloudflare DNS only when using a custom domain.

Backend environment:

- `DATABASE_URL`
- `ENABLE_LLM` (leave unset or false for the deterministic zero-key path)
- `ENABLE_EMBEDDINGS`
- `CORS_ORIGINS`
- `DATASET_MODE=synthetic|official_snapshot`
- `ADMIN_INGESTION_TOKEN` (leave unset to disable public ingestion)
- `OFFICIAL_SNAPSHOT_METADATA`
- `OFFICIAL_QUALITY_REPORT`

Frontend environment:

- `NEXT_PUBLIC_API_BASE_URL` (use `/backend/api` on Vercel Services)
- `NEXT_PUBLIC_SITE_URL` (use the public production alias, for example `https://thai-procurement-intelligence.vercel.app`)
- `NEXT_PUBLIC_DEMO_MODE`

## External LLM request limits

When `ENABLE_LLM=true`, evidence-backed summary and assistant requests that can use an external provider share an in-process limit of five calls per client IP per minute. The API uses `Request.client.host`; it ignores `X-Forwarded-For`. Requests without retrieved evidence return the deterministic no-evidence answer before provider selection. The deterministic mock provider does not consume an external-call slot.

Assistant questions are limited to 500 characters. Assistant filters accept only the documented search fields with bounded text and numeric values. Provider prompts are limited to 24,000 characters. Invalid request fields return `422`, oversized provider input returns `413`, and a rate-limited request returns `429` with `Retry-After`.

The limiter uses process memory. It resets on restart and does not coordinate API instances. Production deployments with multiple instances still need an edge or WAF rate limit for the summary and assistant routes. Behind a proxy, configure that edge limit with its trusted client-IP handling because this application deliberately does not trust forwarded headers.

Ranked semantic and hybrid record searches retain at most the first 5,000 ranked results per request window. They return the exact number of matching candidates and reject pages beyond the window. Keyword search keeps SQL offset pagination and supports `date_desc`, `date_asc`, `budget_desc`, and `budget_asc`. Ranked searches reject `sort` because their order comes from relevance.

The root `vercel.json` defines two services:

- `web`: `apps/web` at `/`
- `api`: `apps/api/main.py` at `/backend`

## Production deployment policy

The existing Vercel project currently tracks `codex/mvp-procurement-intelligence` as its Git production branch. Merges to `main` therefore create preview deployments; production is released manually after verification. Do not promote an existing preview when its environment target is unknown, because promotion does not rebuild the deployment with production configuration.

From a clean checkout of the commit being released, use the linked existing project and run:

```powershell
git rev-parse HEAD
vercel pull --yes --environment=production
$sha = git rev-parse HEAD
vercel deploy --prod --yes --meta githubCommitSha=$sha --meta githubCommitRef=main
```

Before releasing, confirm the SHA, run the API/web/guardrail checks below, and confirm that production environment variable names include `DATABASE_URL` and `DATASET_MODE` without printing their values. After releasing, verify the deployment metadata reports `target=production`, `readyState=READY`, and `githubCommitSha=$sha`; then verify the stable readiness, records, retrieval, and whitespace-validation smoke checks.

Because Vercel strips the service prefix before forwarding to FastAPI, browser requests should use `/backend/api`. The FastAPI service targets Python 3.12. Server-rendered pages also need `NEXT_PUBLIC_SITE_URL`; otherwise a relative API base can resolve through a protected deployment URL and produce fallback zero-data pages.

The summary and cited-answer paths remain deterministic in both local and hosted shapes and require no network inference configuration.

Operational checks:

- Liveness: `/backend/api/health`
- Readiness with database count: `/backend/api/health/readiness`
- Data count smoke: `/backend/api/records?page_size=1`

CI runs on every push and pull request through `.github/workflows/ci.yml` and verifies API tests, lint, migrations, official-snapshot evaluation, repository guardrails, web tests, and production build.

Run ingestion after deployment:

```bash
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```

The hosted production path was verified on 2026-08-24 with `DATASET_MODE=official_snapshot`; `/backend/api/health/readiness` reported `database=ok` and `record_count=250`. Future deployments must re-verify the migration, official import, environment mode, dataset banner, source links, readiness, search, assistant citations, and Data Status page rather than assuming hosted state from repository configuration alone.

The API container applies Alembic migrations before starting. Databases created by an older release may contain the `0001` tables without an `alembic_version` row. Verify that the schema matches the original baseline, then perform the one-time safe baseline and upgrade:

```bash
uv run alembic stamp 0001_initial
uv run alembic upgrade head
```

Do not stamp a database whose baseline schema has not been inspected.
