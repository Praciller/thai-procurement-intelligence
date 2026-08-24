# Thai Public Procurement Intelligence

Evidence-based search and analytics for a bounded Thai public procurement snapshot, with a separate deterministic synthetic demo.

This portfolio project demonstrates CSV ingestion, normalization, search/filtering, analytics, deterministic evidence summaries, semantic-style retrieval, and source-cited Q&A.

## Portfolio review path

The primary review path is local, deterministic, and zero-cost. It requires no inference account or API key. Follow [docs/local_review.md](docs/local_review.md).

Hosted demo: <https://thai-procurement-intelligence.vercel.app>

After local startup, review these areas:

1. Home: confirm English/Thai UI, loaded records, budget metrics, and top projects.
2. Search: filter records, switch keyword/semantic/hybrid modes, and open record details.
3. Dashboard: inspect province, category, monthly, agency, and top-project aggregates.
4. Assistant: ask a procurement question and verify cited evidence.
5. Data Status: confirm readiness, ingestion state, source identity, and record count.

Dataset boundary: `synthetic` remains the default local demo mode. `official_snapshot` uses a separately ingested 250-record DGA/data.go.th snapshot retrieved on 2026-06-21. The current hosted Vercel deployment was verified on 2026-08-24 in `official_snapshot` mode with 250 records. The modes are never aggregated, and the snapshot is not complete, representative, or real-time.

## Screenshots

![Official snapshot home](docs/screenshots/official-home.png)

![Official record provenance](docs/screenshots/official-record-provenance.png)

![Official data quality status](docs/screenshots/official-data-status.png)

Additional search, dashboard, assistant-citation, methodology, and Thai mobile evidence is under [`docs/screenshots/`](docs/screenshots/).

## Features

- Next.js TypeScript frontend with search, record detail, dashboard, assistant, data status, and methodology views.
- English/Thai UI switch using `?lang=en|th`.
- FastAPI backend with health, records, analytics, ingestion, summary, assistant, semantic search, similar-record, and CSV-export endpoints.
- SQLAlchemy schema for procurement records, ingestion runs/errors, summaries, embeddings, and Q&A logs.
- CSV ingestion with validation, normalization, deduplication, and import counters.
- 120 deterministic synthetic records in `data/sample/procurement_sample.csv`.
- Approved 250-record bounded public snapshot with checksum, mapping, quality reports, record-level provenance, and idempotent import.
- Visible bilingual dataset identity, source attribution, freshness, and data-quality status.
- Deterministic evidence summaries and cited answers that require no network inference.
- Local deterministic embeddings for semantic/hybrid retrieval demos.
- Docker Compose with PostgreSQL JSON vector storage, API, and web services; similarity runs in application code.

## Architecture

```mermaid
flowchart LR
  CSV["CSV / public source"] --> Import["FastAPI ingestion"]
  Import --> DB[("PostgreSQL JSON vector storage")]
  DB --> API["FastAPI REST API"]
  API --> Web["Next.js frontend"]
  API --> Answer["Deterministic evidence summaries"]
  API --> Search["Keyword + semantic retrieval"]
  Answer --> Evidence["Citations and retrieved records"]
```

## Local setup

Full Windows PowerShell steps, smoke checks, expected results, and troubleshooting: [docs/local_review.md](docs/local_review.md).

Prerequisites:

- Node.js 24+
- `uv`
- Docker Desktop for the PostgreSQL path

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Backend:

```bash
cd apps/api
uv sync
```

Run PostgreSQL and API:

```bash
docker compose up db
cd apps/api
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/thai_procurement"
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

Seed deterministic sample records:

```bash
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```

Frontend API configuration:

```bash
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api"
npm run dev
```

Local endpoints:

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

## Environment variables

Backend:

- `DATABASE_URL`
- `ENABLE_EMBEDDINGS`
- `CORS_ORIGINS`
- `DATASET_MODE=synthetic|official_snapshot`
- `ADMIN_INGESTION_TOKEN`
- `OFFICIAL_SNAPSHOT_METADATA`
- `OFFICIAL_QUALITY_REPORT`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_DEMO_MODE`

## Deterministic answer design

Search, dashboard, details, export, ingestion, summaries, and evidence retrieval all work without external inference. Summary output is cached in `ai_summaries`; assistant answers are generated from retrieved records and return citations alongside the answer. The public answer path is designed for reproducible portfolio review rather than unconstrained generation.

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

The judged retrieval evaluation regenerated on 2026-08-24 uses eight frozen queries (seven positive and one negative control) against the committed 250-record snapshot. Keyword and hybrid retrieval both measured mean Precision@5 `0.7714`, Recall@5 `0.4929`, nDCG@5 `0.8571`, and MRR `0.8571`. Keyword returned zero results for the negative control; hybrid returned five false positives, so the deterministic hash-vector path is documented as an architecture/demo baseline rather than production semantic retrieval. Citation and source-link completeness remained `1.0`, the second import left all 250 records unchanged, and the forbidden-claim-term rate remained `0.0`. See [quality](reports/official_snapshot/data_quality_summary.md), [evaluation](reports/official_snapshot/evaluation.md), and the [judgment set](evals/retrieval/official_snapshot_judgments.json).

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

GitHub Actions runs API tests, migration checks, official-snapshot evaluation, repository guardrails, web tests, lint, and production build on every push and pull request.

## Optional deployment

The hosted deployment is optional. The local review path remains the canonical zero-key path. See [docs/deployment.md](docs/deployment.md) and [docs/security.md](docs/security.md).

## Known limitations

- Excel ingestion is an extension point, not implemented in the MVP.
- Deterministic local embeddings are a no-cost semantic demo, not production-grade embeddings.
- The official fixture is a small non-random subset from one source resource part.
- The portal's attribution license label does not specify a version.
- Public ingestion is disabled unless a server-side admin token is explicitly configured.
- The hosted deployment currently serves the bounded official snapshot; re-check readiness and Data Status after future deployments because hosted state can change independently of the repository.
- Public data is not proof of fraud, corruption, misconduct, or suspicious behavior.

## Portfolio bullet

Built a zero-cost Next.js/FastAPI procurement intelligence case study with a checksummed 250-record official DGA snapshot, versioned mapping, provenance-aware PostgreSQL ingestion, deterministic quality/retrieval evaluation, bilingual evidence UI, and source-cited answers while preserving an isolated synthetic demo.
