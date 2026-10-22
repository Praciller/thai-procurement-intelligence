# Release candidate validation checklist

This is an operator checklist, not a release approval. The project currently has a series of stacked Draft PRs; passing an isolated job does not authorize a production deployment.

## Proposed review order

`#26 → #29 → #27 → #28 → #30 → #31 → #32 → #33 → #34`.

The base branch of every stacked PR must point to its immediate predecessor until that predecessor is merged. After each merge, check the next PR's base, changed files, mergeability and **current head SHA**. Do not rely on old CI results if head/base changes.

## Code and evidence gates

- [ ] All PRs remain Draft until a reviewer accepts the change set; no automated merge.
- [ ] `api`, `web`, `e2e`, and `guardrails` are **successful for the current PR head/base**. Queued, canceled, and in-progress checks are not pass.
- [ ] Run `uv run pytest -q` and `uv run ruff check .` in `apps/api`.
- [ ] Run `npm run web:test`, `npm run web:lint`, and `npm run web:build` at repository root.
- [ ] Run `python scripts/check_repo_guardrails.py`.
- [ ] Rerun `python -m app.jobs.evaluate_official_snapshot` from `apps/api` and ensure committed evaluation artifacts show **no unexplained drift**. The frozen benchmark has only 8 judged queries (7 positive, 1 negative) against a non-random 250-record source snapshot; do not advertise population-wide retrieval quality.
- [ ] Review changes in `reports/official_snapshot/` and maintain the distinction between original-file checksum verification and mere database-provenance consistency.
- [ ] Manually verify keyboard skip navigation, responsive search results, filters and both supported UI languages; a smoke test is not a full WCAG audit.

## Database and infrastructure gates

- [ ] Keep `ENABLE_LLM=false` during initial deployment. Do not configure or disclose external API keys in PRs, logs, test reports, or client-side code.
- [ ] Take and verify a restorable production database backup **before** schema changes.
- [ ] Rehearse `alembic upgrade head` (through revision `0003_ai_hourly_budget`) on an isolated PostgreSQL 16 database, starting from revision `0002` **with existing records**; verify records survive and repeat `upgrade head` without changing anything. SQLite-only evidence is not sufficient.
- [ ] Confirm API startup and CLI import/embedding/summarization jobs do **not** create or migrate schemas implicitly. Alembic must be applied explicitly before starting the API or running jobs.
- [ ] If an earlier runtime created `ai_hourly_budget` while Alembic still reports `0002`, migration `0003` validates the existing column and key structure and adopts it only when identical. Treat schema mismatch as an explicit stop rather than using `alembic stamp` or dropping tables blindly.
- [ ] Verify runtime database privileges and backup/restore procedure. Do not run `alembic downgrade` automatically on a database containing new data.
- [ ] Set explicit `AI_HOURLY_REQUEST_LIMIT` and keep `LOG_AI_QUERIES=false` if a later release enables external LLMs. The budget counts *external-capable requests*, not every provider retry, so authentication/edge abuse protection may still be needed.
- [ ] Check CORS and public write endpoints against the intended deployment threat model before exposing external inference.
- [ ] Check synthetic/official dataset isolation and freshness of the official data-source snapshot.

## Post-deployment and rollback

- [ ] Deploy only after separate, explicit approval; record deployed Git SHA, environment and release time.
- [ ] Smoke-test health/readiness, search (keyword and hash-grounded semantic), records, assistant mock, data-status provenance and CSV export in the target environment.
- [ ] Confirm error/empty/loading states behave correctly when the API is unavailable.
- [ ] Monitor request errors, database errors, external-inference permit usage and abnormal response times; do not log raw user questions by default.
- [ ] If checks fail, stop the rollout and revert the application deployment to the recorded previous SHA. Restore database from the verified backup if a schema/data rollback is truly necessary and separately approved.

## Known limitations

Local hash-based vectors are not validated Thai-language semantic embeddings. Ranked semantic/hybrid pagination is not implemented beyond the first page; unsupported pages must produce a clear error. The official snapshot is deliberately limited and should not be presented as a complete view of Thai public procurement.

## Isolated PostgreSQL 16 rehearsal evidence (2026-10-23)

The following was executed locally using a **disposable PostgreSQL 16 Alpine Docker container** and a temporary Git checkout; it was not run against production:

- Reproduced the original failure: an import script at Alembic revision `0002` invoked ORM `create_all`, prematurely creating the `ai_hourly_budget` table. The original `0003` migration then failed with PostgreSQL `DuplicateTable`.
- Updated startup/import/embedding/summarization so only explicit Alembic migrations manage runtime schema.
- Confirmed migration `0002 → 0003` can adopt an already-existing **structurally identical** budget table without dropping data, and rejects a mismatched table.
- Confirmed a second clean database can import 120 records at revision `0002` without creating the future budget table, then upgrade successfully to `0003` and retain all 120 records.
- Verified a repeated `alembic upgrade head` completes without schema changes.
- Reproduced psycopg returning `rowcount=-1` for `INSERT .. ON CONFLICT`; switched permit detection to SQL `RETURNING`.
- With 24 concurrent PostgreSQL permit requests and a limit of 5, exactly 5 succeeded, 19 were denied and the database stored 5.
- Python regression suite: 104 passed, Ruff passed. CI additionally now includes a PostgreSQL migration-before-browser check and quota concurrency check.

**Still required before production:** identify the actual production PostgreSQL version, verify a restorable backup and migration privileges, inspect migration differences on a replica, and obtain explicit deploy authorization. The rehearsal does not establish production readiness by itself.
