# Portfolio Review Guide

This project is ready to review locally as a zero-cost portfolio demo for AI Engineer and Data Engineer roles.

## What To Review

- Primary local flow: [local_review.md](local_review.md)
- Optional live app: <https://thai-procurement-intelligence.vercel.app>
- Optional hosted readiness: <https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness>
- CI workflow: `.github/workflows/ci.yml`
- Architecture: [architecture.md](architecture.md)
- Deployment: [deployment.md](deployment.md)
- Data source boundary: [data-source.md](data-source.md)
- Provenance policy: [data_provenance.md](data_provenance.md)
- Official source approval: [official_source_review.md](official_source_review.md)
- Official mapping and measured quality: [official_source_mapping.md](official_source_mapping.md), [data_quality.md](data_quality.md)
- Synthetic data dictionary: [synthetic_dataset.md](synthetic_dataset.md)
- Security checklist: [security.md](security.md)

## Local Demo Path

Start with [local_review.md](local_review.md). It requires no hosted services or API keys.

1. Home: verify English and Thai UI, loaded metrics, and top procurement records.
2. Search: filter by keyword, province, category, sort order, and retrieval mode.
3. Record detail: inspect normalized fields, raw source text, similar records, and AI summary.
4. Dashboard: review aggregate metrics by province, category, month, agency, and project.
5. Assistant: ask a natural-language question and inspect cited evidence.
6. Data Status: verify ingestion and production readiness counters.

## Engineering Signals

- Monorepo with Next.js frontend and FastAPI backend.
- Local PostgreSQL persistence through Docker Compose.
- Optional Vercel/Supabase deployment that is not part of the default review path.
- English/Thai multilingual UI.
- Server-rendered dashboard and home data.
- Search modes: keyword, semantic-style fallback, hybrid.
- LLM provider abstraction: mock, Gemini, OpenRouter.
- Evidence-limited assistant responses with citations.
- Ingestion run/error tracking.
- Checksummed 250-record official snapshot with idempotent import and record-level provenance.
- Bilingual dataset identity, freshness, source links, and quality evidence.
- CI on every push and pull request.
- Tests cover API flows, ingestion behavior, DB connection config, API URL resolution, and locale links.

## Honest Boundaries

- The hosted demo remains synthetic until separately migrated and verified.
- The local official mode is a bounded non-random snapshot, not complete or representative evidence.
- Local deterministic embeddings are a no-cost semantic demo, not production-grade vector embeddings.
- Public ingestion is disabled by default and requires a server-side token.
- Public data is not proof of wrongdoing.
- Exposed provider keys must be rotated if they were pasted into chat or logs.

## Expected Local Evidence

Expected readiness shape:

```json
{
  "status": "ready",
  "database": "ok",
  "record_count": 120
}
```

Verify locally:

```bash
npm run web:test
npm run web:lint
npm run web:build
npm run api:test
python scripts/check_repo_guardrails.py
```

The hosted demo may be checked after the local flow, but it is not evidence that the repository can run without hosted dependencies.
