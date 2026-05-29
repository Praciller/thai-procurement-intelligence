# Thai Public Procurement Intelligence

AI-powered search and analytics platform for Thai public procurement open data.

This is a personal portfolio project for AI Engineer and Data Engineer roles. It demonstrates CSV ingestion, normalization, search/filtering, analytics, optional LLM summarization, semantic-style retrieval, and evidence-based Q&A.

## Features

- Next.js TypeScript frontend with records search, detail pages, dashboard, assistant, data status, and methodology pages.
- English/Thai UI switch using `?lang=en|th`, with localized navigation, page copy, record tables, metrics, and loading states.
- FastAPI backend with health, records, analytics, ingestion, summary, assistant, semantic search, similar records, and CSV export endpoints.
- SQLAlchemy schema for procurement records, ingestion runs/errors, AI summaries/extractions, embeddings, and Q&A logs.
- CSV ingestion with validation, normalization, deduplication, and import counters.
- 120 synthetic sample records in `data/sample/procurement_sample.csv`.
- Optional LLM provider abstraction for Gemini, OpenRouter, and deterministic local mock.
- Local deterministic embeddings for free semantic/hybrid retrieval demos.
- Docker Compose with PostgreSQL/pgvector, API, and web services.

## Architecture

```mermaid
flowchart LR
  CSV["CSV / Public source"] --> Import["FastAPI ingestion"]
  Import --> DB[("PostgreSQL / pgvector")]
  DB --> API["FastAPI REST API"]
  API --> Web["Next.js frontend"]
  API --> LLM["Gemini / OpenRouter / mock"]
  API --> Search["Keyword + semantic fallback"]
```

## Production Demo

- App: <https://thai-procurement-intelligence.vercel.app>
- API health: <https://thai-procurement-intelligence.vercel.app/backend/api/health>
- API readiness: <https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness>

The production deployment uses Vercel Services for the Next.js and FastAPI services and Supabase PostgreSQL for persistence. `NEXT_PUBLIC_SITE_URL` must point at the public Vercel alias so server-rendered pages can fetch `/backend/api` without hitting protected deployment URLs.

## Local Setup

Prerequisites:

- Node.js 24+
- `uv`
- Docker Desktop for PostgreSQL path

Install frontend deps:

```bash
cd apps/web
npm install
```

Install backend deps:

```bash
cd apps/api
uv sync
```

Run PostgreSQL:

```bash
docker compose up db
```

Run API:

```bash
cd apps/api
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/thai_procurement"
uv run uvicorn app.main:app --reload --port 8000
```

Seed sample records:

```bash
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```

Run frontend:

```bash
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api"
npm run dev
```

Open:

- Web app: <http://localhost:3000>
- API docs: <http://localhost:8000/api/docs>

## Docker Compose

```bash
docker compose up --build
```

Then seed data:

```bash
docker compose exec api uv run python -m app.jobs.import_csv --file /data/sample/procurement_sample.csv --source sample
```

## Environment Variables

Backend:

- `DATABASE_URL`
- `LLM_PROVIDER=mock|gemini|openrouter`
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `ENABLE_LLM`
- `ENABLE_EMBEDDINGS`
- `AI_RATE_LIMIT_PER_HOUR`
- `CORS_ORIGINS`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_DEMO_MODE`

## AI Design

AI features are optional. If no API key is configured, search, dashboard, details, export, ingestion, and evidence retrieval still work. Summaries are cached in `ai_summaries`; assistant answers cite retrieved records.

## Data Source

The committed sample dataset is synthetic and clearly labeled. It uses names such as `Sample Provincial Office A` and `Sample Vendor B` to avoid claims about real agencies.

## Tests

```bash
cd apps/api
uv run pytest

cd ../..
npm run web:test
npm run web:lint
npm run web:build
```

GitHub Actions runs API tests, web unit tests, lint, and production build on every push and pull request.

## Deployment

Recommended:

- Frontend and backend: one Vercel Services project
- Database: Supabase PostgreSQL
- Scheduled ingestion: GitHub Actions or provider scheduler

See [docs/deployment.md](docs/deployment.md).
See [docs/security.md](docs/security.md) for secret rotation and production smoke checks.

## Known Limitations

- Excel ingestion is an extension point, not implemented in MVP.
- Deterministic local embeddings are a no-cost semantic demo, not production-grade embeddings.
- No auth or private admin surface is included.
- Sample data is not real procurement evidence.
- Public Thai procurement data ingestion still needs a selected official source, mapping review, and provenance policy before replacing the synthetic sample dataset.

## Portfolio Bullet

Built an end-to-end AI/data platform for Thai public procurement open data using Next.js, FastAPI, SQLAlchemy, PostgreSQL-compatible persistence, and Gemini/OpenRouter provider abstractions. Implemented ingestion, normalization, search, semantic-style retrieval, dashboard analytics, AI summarization, and evidence-based Q&A with free-tier deployment constraints.
