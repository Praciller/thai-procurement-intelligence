# Zero-Cost Local Review

This is the primary portfolio review path. It uses the committed synthetic CSV, local PostgreSQL, deterministic embeddings, and the mock LLM provider. No hosted service or API key is required.

## Prerequisites

- Docker Desktop
- Node.js 24+
- `uv`

Run each block from the repository root in Windows PowerShell.

## Install

```powershell
cd apps/api
uv sync --locked
cd ../web
npm ci
cd ../..
```

## Start PostgreSQL

```powershell
docker compose up -d db
docker compose ps
```

Expected: `db` is `healthy` and port `5432` is published.

## Initialize and Seed

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/thai_procurement"
$env:LLM_PROVIDER="mock"
$env:ENABLE_LLM="false"
$env:ENABLE_EMBEDDINGS="true"
cd apps/api
uv run python -m app.jobs.import_csv --file ../../data/sample/procurement_sample.csv --source sample
uv run python -m app.jobs.generate_embeddings --limit 1000
```

Expected: the import reports 120 total rows with no failures on a fresh database; reruns update or deduplicate records. Embedding output reports 120 records.

## Start API and Web

Terminal 1:

```powershell
cd apps/api
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/thai_procurement"
$env:LLM_PROVIDER="mock"
$env:ENABLE_LLM="false"
$env:ENABLE_EMBEDDINGS="true"
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```powershell
cd apps/web
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000/api"
$env:NEXT_PUBLIC_DEMO_MODE="true"
npm run dev
```

Open Home, Search, Dashboard, Assistant, Data Status, and Methodology at <http://localhost:3000>. Verify the synthetic-data notice remains visible and Assistant returns cited records without an API key.

## API Smoke Checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/health/readiness
Invoke-RestMethod 'http://127.0.0.1:8000/api/records?page_size=1'
Invoke-RestMethod http://127.0.0.1:8000/api/analytics/overview
$body = @{ question = 'highest budget IT project'; limit = 4 } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/assistant/ask -Method Post -ContentType 'application/json' -Body $body
```

Expected readiness: `status=ready`, `database=ok`, `record_count=120`. Records and analytics return synthetic sample data; Assistant returns citations and `ai_enabled=false` because the deterministic mock is not an external LLM.

## Verification

```powershell
cd apps/api
uv run pytest
cd ../..
npm run web:test
npm run web:lint
npm run web:build
docker compose config --quiet
```

## Troubleshooting

- Port conflict: stop the service using 3000, 5432, or 8000, or change the published port.
- Stale database: `docker compose down` preserves the named volume. Use `docker compose down -v` only when intentionally deleting local demo data.
- Windows temporary-path failure:

```powershell
New-Item -ItemType Directory -Force C:\tmp\thai-procurement-temp | Out-Null
$env:TEMP="C:\tmp\thai-procurement-temp"
$env:TMP=$env:TEMP
$env:PYTEST_ADDOPTS="--basetemp=C:/tmp/pytest-thai-procurement"
```
