# Thai Public Procurement Intelligence

Evidence-based search and analytics for a bounded Thai public procurement snapshot, with a separate deterministic synthetic demo.

This is a personal portfolio project for AI Engineer and Data Engineer roles. It demonstrates CSV ingestion, normalization, search/filtering, analytics, optional LLM summarization, semantic-style retrieval, and evidence-based Q&A.

## Portfolio Review Path

The primary review path is local, deterministic, and zero-cost. It requires no API keys, Vercel, Supabase, Gemini, or OpenRouter. Follow [docs/local_review.md](docs/local_review.md).

The hosted demo is optional: <https://thai-procurement-intelligence.vercel.app>

After local startup, open these in order:

1. Home: confirm English/Thai UI, 120 loaded records, budget metrics, and top projects.
2. Search: filter records, switch keyword/semantic/hybrid modes, open a record detail.
3. Dashboard: scan province, category, monthly, agency, and top-project aggregates.
4. Assistant: ask a procurement question and check cited evidence.
5. Data Status: confirm readiness, ingestion run, and record count.

Dataset warning: `synthetic` remains the default and the optional hosted demo has not been migrated in this change. Local `official_snapshot` mode uses a separately ingested 250-record DGA/data.go.th snapshot retrieved on 2026-06-21. The modes are never aggregated, and the snapshot is not complete, representative, or real-time.

## Screenshots

![Official snapshot home](docs/screenshots/official-home.png)

![Official record provenance](docs/screenshots/official-record-provenance.png)

![Official data quality status](docs/screenshots/official-data-status.png)

The complete evidence set includes search, dashboard, assistant citations, methodology, and Thai mobile views under [`docs/screenshots/`](docs/screenshots/).

## Features

- Next.js TypeScript frontend with records search, detail pages, dashboard, assistant, data status, and methodology pages.
- English/Thai UI switch using `?lang=en|th`, with localized navigation, page copy, record tables, metrics, and loading states.
- FastAPI backend with health, records, analytics, ingestion, summary, assistant, semantic search, similar records, and CSV export endpoints.
- SQLAlchemy schema for procurement records, ingestion runs/errors, AI summaries/extractions, embeddings, and Q&A logs.
- CSV ingestion with validation, normalization, deduplication, and import counters.
- 120 synthetic sample records in `data/sample/procurement_sample.csv`.
- Approved 250-record official bounded snapshot with checksum, mapping, quality reports, record-level provenance, and idempotent import.
- Visible bilingual dataset identity, source attribution, freshness, and data-quality status.
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

## Optional Hosted Demo

- App: <https://thai-procurement-intelligence.vercel.app>
- API health: <https://thai-procurement-intelligence.vercel.app/backend/api/health>
- API readiness: <https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness>
- Portfolio guide: [docs/portfolio-review.md](docs/portfolio-review.md)

The current optional deployment uses Vercel Services and Supabase PostgreSQL. Neither is required for review. `NEXT_PUBLIC_SITE_URL` must point at the public Vercel alias so server-rendered pages can fetch `/backend/api` without hitting protected deployment URLs.

## Local Setup

Full Windows PowerShell steps, smoke checks, expected results, and troubleshooting: [docs/local_review.md](docs/local_review.md).

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
uv run alembic upgrade head
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
- `DATASET_MODE=synthetic|official_snapshot`
- `ADMIN_INGESTION_TOKEN`
- `OFFICIAL_SNAPSHOT_METADATA`
- `OFFICIAL_QUALITY_REPORT`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_DEMO_MODE`

## AI Design

AI features are optional. If no API key is configured, search, dashboard, details, export, ingestion, and evidence retrieval still work. Summaries are cached in `ai_summaries`; assistant answers cite retrieved records.

## Official bounded snapshot

- Publisher: Digital Government Development Agency (Public Organization), with source-data cooperation stated by the portal.
- Dataset: [fiscal-year 2568 EGP contract data](https://data.go.th/dataset/3beb7813-3607-4e5f-a094-b3b574a6e358).
- Retrieved: 2026-06-21T14:02:45.343910Z.
- Coverage in this subset: 2024-10-04 through 2025-09-29.
- Records: 250 unique source project IDs.
- License label: `Creative Commons Attributions` (the portal does not supply a version or URL).
- SHA-256: `413f70c0ef17c17233b99aa42a7f1e25284644948c37bd109c21e9cc0678618b`.

Source governance, mapping, acquisition, and limitations: [source review](docs/official_source_review.md), [mapping](docs/official_source_mapping.md), [snapshot](docs/official_snapshot.md), [provenance](docs/data_provenance.md), and [limitations](docs/limitations.md).

## Measured evidence

The deterministic evaluation on 2026-06-22 measured 250/250 valid rows, zero rejected/duplicate/warning rows, an idempotent second import with 250 unchanged rows, keyword precision@5 of 1.0, hybrid precision@5 of 0.5, citation/source-link completeness of 1.0, and unsupported-claim rate of 0.0 across four labeled queries. These are bounded-fixture results, not production-scale claims. See [quality](reports/official_snapshot/data_quality_summary.md) and [evaluation](reports/official_snapshot/evaluation.md).

## Official snapshot local mode

```powershell
cd apps/api
$env:DATASET_MODE="official_snapshot"
uv run alembic upgrade head
uv run python -m app.jobs.import_official_snapshot --file ../../data/official/raw/dga-egp-contract-2568-250.csv --metadata ../../data/official/metadata/dga-egp-contract-2568-250.json
uv run uvicorn app.main:app --reload --port 8000
```

Synthetic mode remains `DATASET_MODE=synthetic`; use a separate database when switching modes for the clearest local review.

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

## Optional Deployment

Optional hosted configuration:

- Frontend and backend: one Vercel Services project
- Database: Supabase PostgreSQL
- Scheduled ingestion: GitHub Actions or provider scheduler

See [docs/deployment.md](docs/deployment.md).
See [docs/security.md](docs/security.md) for secret rotation and production smoke checks.

## Known Limitations

- Excel ingestion is an extension point, not implemented in MVP.
- Deterministic local embeddings are a no-cost semantic demo, not production-grade embeddings.
- The official fixture is a small non-random subset from one source resource part.
- The portal's attribution license label does not specify a version.
- Public ingestion is disabled unless a server-side admin token is explicitly configured.
- The hosted deployment remains synthetic until separately migrated and verified.
- Public data is not proof of fraud, corruption, misconduct, or suspicious behavior.

## Portfolio Bullet

Built a zero-cost Next.js/FastAPI procurement intelligence case study with a checksummed 250-record official DGA snapshot, versioned mapping, provenance-aware PostgreSQL ingestion, deterministic quality/retrieval evaluation, bilingual evidence UI, and source-cited assistant responses while preserving an isolated synthetic demo.
