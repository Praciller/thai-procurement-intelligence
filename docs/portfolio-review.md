# Portfolio Review Guide

This project is ready to show as a portfolio demo for AI Engineer and Data Engineer roles.

## What To Review

- Live app: <https://thai-procurement-intelligence.vercel.app>
- API readiness: <https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness>
- CI workflow: `.github/workflows/ci.yml`
- Architecture: [architecture.md](architecture.md)
- Deployment: [deployment.md](deployment.md)
- Data source boundary: [data-source.md](data-source.md)
- Security checklist: [security.md](security.md)

## Demo Path

1. Home: verify English and Thai UI, loaded metrics, and top procurement records.
2. Search: filter by keyword, province, category, sort order, and retrieval mode.
3. Record detail: inspect normalized fields, raw source text, similar records, and AI summary.
4. Dashboard: review aggregate metrics by province, category, month, agency, and project.
5. Assistant: ask a natural-language question and inspect cited evidence.
6. Data Status: verify ingestion and production readiness counters.

## Engineering Signals

- Monorepo with Next.js frontend and FastAPI backend.
- Supabase PostgreSQL production persistence.
- Vercel Services deployment for frontend and API.
- English/Thai multilingual UI.
- Server-rendered dashboard and home data.
- Search modes: keyword, semantic-style fallback, hybrid.
- LLM provider abstraction: mock, Gemini, OpenRouter.
- Evidence-limited assistant responses with citations.
- Ingestion run/error tracking.
- CI on every push and pull request.
- Tests cover API flows, ingestion behavior, DB connection config, API URL resolution, and locale links.

## Honest Boundaries

- Dataset is synthetic demo data, not real procurement evidence.
- Real Thai public procurement ingestion needs final official source selection and mapping review.
- Local deterministic embeddings are a no-cost semantic demo, not production-grade vector embeddings.
- No private admin/auth surface is included.
- Exposed provider keys must be rotated if they were pasted into chat or logs.

## Current Production Smoke Result

Expected readiness shape:

```json
{
  "status": "ready",
  "database": "ok",
  "record_count": 120
}
```

Run locally:

```bash
npm run web:test
npm run web:lint
npm run web:build
npm run api:test
```
