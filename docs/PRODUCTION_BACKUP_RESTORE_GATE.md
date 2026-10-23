# Production Backup, Restore and Release Gate — 2026-10-23

> **Operator-only handoff. Not authorization to run SQL, switch traffic, or deploy.**
> Never commit backups, database URLs, passwords, API keys, screenshots with secrets, or `.env` files to Git.
> Store exports outside the repository in an encrypted, access-controlled location with an independent off-device copy.

## Verified production baseline (read-only)

| Item | Observed |
| --- | --- |
| Supabase project | `thai-procurement-intelligence` (`eojfchphzmgspybmugzq`) |
| PostgreSQL | `17.6` (Singapore / `ap-southeast-1`) |
| Alembic | `0002_official_provenance` |
| Stored records | `370` total; `250` with `dataset_type=official_snapshot` |
| `ai_hourly_budget` | Does not yet exist |
| Hosted stable endpoint | `https://thai-procurement-intelligence.vercel.app` |
| Stable API | `/backend/api/health`, `/backend/api/dataset/status`, `/backend/api/records?page_size=1` |
| Source state | `official_snapshot`, `stale_snapshot`, 250 official records |
| Release candidate | Draft PR #44, reviewed head `e44a0b715bb881e17397dcb780b627b3c49fab8d` |

The checks above do **not** mean a new release has happened. A previously deployed Vercel production build remains in service. The project is linked to GitHub; **assume main merges may trigger automation** until deployment targeting and production branch mapping are explicitly verified.

## Gate A: verified, restorable backup — BLOCKED

Supabase documents that the **Free plan has no guaranteed scheduled database backups**. Export a logical snapshot before any new production migrations. The connected Supabase tools in this review do not provide a database-backup export or restore action; the workstation had no authenticated Supabase CLI available during inspection.

1. On the trusted operator computer, install/verify the official Supabase CLI and Docker Desktop; authenticate interactively with `supabase login` and link the exact production project with `supabase link --project-ref eojfchphzmgspybmugzq`. Never paste credentials in ChatGPT or into repository files.
2. Create a **private local backup folder outside Git/OneDrive public sharing** and record the UTC timestamp and project reference. Run the following commands **inside that folder**, using an already authenticated/link-confirmed CLI:

   ```sh
   supabase db dump -f roles.sql --role-only
   supabase db dump -f schema.sql
   supabase db dump -f data.sql --use-copy --data-only
   ```

3. Check all three files are present, nonempty, owned by the intended user, and not tracked by Git. Check that the data dump covers this app's tables, including `procurement_records`, `ai_summaries`, `procurement_embeddings`, `ingestion_runs` and `alembic_version`.
4. Encrypt the files; keep an independent off-device copy and record checksum hashes, timestamp and a private backup reference **without posting credentials or backup contents**.
5. Restore the three-file export into an **isolated matching-version test environment**, following official Supabase documentation. Supabase CLI dumps **exclude Supabase-managed internal schemas by default**, so do not call this a full project backup and do not restore over production. Bring any required extensions, roles, triggers, and privileges into the test environment before restore.
6. Verify the restored environment independently: `370` total records, `250` official records, Alembic `0002_official_provenance`, expected table schemas, sample source checksums and record counts; confirm application read paths. Treat restore errors or count mismatches as a **STOP**.
7. Record a private restoration log and evidence that the backup can be used (backup ID, creation time, test restore time and verification results). Only then mark Gate A complete.

Official guidance:
- <https://supabase.com/docs/guides/platform/backups>
- <https://supabase.com/docs/reference/cli/supabase-db-dump>
- <https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore>

## Gate B: database/permission preflight — NOT APPROVED

**No production DDL has been run**. The changes requiring Alembic `0003_ai_hourly_budget` passed independent PostgreSQL 16 and **PostgreSQL 17 Alpine** local rehearsals. With 120 seeded test records, `0002 -> 0003` preserved 120/120; 24 parallel budget requests permitted 5 and denied 19; repeated upgrade was idempotent. These are **synthetic rehearsal databases**, not a restoration of the production database.

Before the migration, ensure the production app DB role can read and write the new table and that the live Supabase event trigger `ensure_rls` does not unexpectedly block usage under the app's runtime role. That event trigger automatically enables RLS on new tables in `public`. Identify the runtime DB role **without exposing a password or connection string**.

Current security-advisor triage (read-only):
- Eight existing `public` application tables have RLS enabled and no policies. Explicit permission checks indicate **neither `anon` nor `authenticated` currently has SELECT privilege** on these tables; no public read exposure was established from those findings. Do not blindly add permissive policies.
- `public.rls_auto_enable()` is an event-trigger `SECURITY DEFINER` function attached to `ensure_rls`; `anon` and `authenticated` inherit EXECUTE. Supabase warns about broad EXECUTE. Review whether to revoke public execution in a **separate, tested, rollbackable security change**, while preserving event-trigger behavior. Do not drop the function or event trigger to silence a warning.

References:
- <https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy>
- <https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable>

## Gate C: preview/API access — PARTIALLY VERIFIED

PR #44 GitHub API, web, e2e, and guardrails checks passed. A Vercel Preview deployment was **READY** for the release branch after explicit `nextjs` / `fastapi` service framework pins fixed `MULTIPLE_FRAMEWORKS_SERVICE`. This proves build completion, **not** authenticated API/database operation.

### Authenticated runtime findings — 2026-10-24

Using the connected Vercel account's **protected-deployment fetch** (without sharing any access-bypass link or weakening project protection), the exact release preview deployment `dpl_H1Sjr6FnKXCYKKJNR8ctpYSq8NdB` returned:

| Preview endpoint | Status | Meaning |
| --- | --- | --- |
| `/` | 200 | Next.js HTML is served |
| `/backend/api/health` | 200 | FastAPI process responds; **not** DB readiness |
| `/backend/api/health/readiness` | 503 | JSON `database unavailable` |
| `/backend/api/dataset/status` | 500 | SQLAlchemy DB connection fails |
| `/backend/api/records?page_size=1` | 500 | SQLAlchemy DB connection fails |
| `/records?lang=th` | 200 | Correct Thai API-unavailable and unknown-dataset messaging |
| `/dashboard?lang=en` | 200 | Correct English API-unavailable and unknown-dataset messaging |
| `/data-status?lang=th` | 200 | Correct Thai API-unavailable and unknown-dataset messaging |

Vercel runtime logs show SQLAlchemy failing to connect on dataset and records routes. **Configuration evidence**: `DATABASE_URL`, `NEXT_PUBLIC_API_BASE_URL`, `DATASET_MODE` and the external LLM settings are currently scoped to **production only**, not Preview. With no Preview `DATABASE_URL`, the API falls back to its local SQLite default `sqlite:///./thai_procurement_demo.db`, which does not provide a ready migrated persistent database in serverless Preview. The full exception cause was not independently established; the missing Preview DB configuration and 503 readiness are verified.

**Do not copy or expose Production `DATABASE_URL` to Preview.** Provision an independently isolated Preview database (subject to explicit resource/cost approval), apply `alembic upgrade head` and seed only **synthetic fixture** rows. Set Preview-only `DATABASE_URL`, `NEXT_PUBLIC_API_BASE_URL=/backend/api`, `DATASET_MODE=synthetic`, `ENABLE_LLM=false` and `LOG_AI_QUERIES=false`. No external model credentials should be enabled in Preview. Redeploy **Preview only** and recheck the endpoints above plus the Browser E2E flow.

This is a **confirmed release blocker**, not a reason to change the production database. Protected Preview access is solved; **Preview database readiness is not**.

For an authorized preview session, verify:
- HTML route, server-rendered data widgets, all major EN/TH screens and accessible keyboard flows
- `/backend/api/health`, `/backend/api/health/readiness`, `/backend/api/dataset/status`, `/backend/api/records?page_size=1`
- Correct API prefix (`/backend/api`), dataset identity, false-empty failure behavior and source citations
- Safe mock-only Q&A and LLM settings, without external provider keys in a preview

## Gate D: controlled rollout / rollback — NOT AUTHORIZED

1. Record exactly **which Git commit** is approved and what deployment branch Vercel considers production. Never assume that a protected merge means deployments are disabled.
2. Freeze schema/data changes, take the **verified Gate A backup**, inspect migrations against the actual production database, and ensure rollback/restore instructions are operational.
3. Keep `ENABLE_LLM=false`, `LOG_AI_QUERIES=false`; do not assume the global hourly budget is per-user authentication/rate limiting.
4. Merge/deploy only after explicit release approval. If the merge triggers an automatic deployment, ensure this trigger is intentionally approved and monitored.
5. After migration and release, verify Alembic `0003`, count `370` total / `250` official before any intentional ingestion, health/readiness, citations, language, fallback behavior, and errors.
6. Restore production traffic to the previously recorded deployment on failure; database rollback may need the verified logical backup. **Never drop `ai_hourly_budget` or run `alembic downgrade` blindly** when live data has been written.

**Current decision: HOLD production merge/deployment and schema migration until Gates A and C are verified.**

## Workstation CLI readiness — 2026-10-24

On `pracill`, Docker is reachable and the official Supabase CLI can run through `npx --yes supabase` (verified version `2.122.0`). The CLI has **not** been authenticated: its read-only `projects list` reports that an access token is required. No token or connection string was inspected or printed. After the operator signs in interactively on that trusted computer, use the documented export/restore procedure above. The Supabase connector's API authorization cannot be assumed to transfer to an unrelated local CLI session.
