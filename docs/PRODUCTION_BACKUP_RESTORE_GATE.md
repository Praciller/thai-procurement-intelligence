# Production Backup, Restore and Release Gate — 2026-10-24

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
| Release candidate | Draft PR #44; use the current PR head and current CI status |

The checks above do **not** mean a new release has happened. A previously deployed Vercel production build remains in service. The project is linked to GitHub; **assume main merges may trigger automation** until deployment targeting and production branch mapping are explicitly verified.

## Gate A: logical backup exported; restore and portability — BLOCKED

Supabase documents that the **Free plan has no guaranteed scheduled database backups**. On 2026-10-24, authenticated Supabase CLI access on `pracill` became available, and a production logical export was completed and encrypted. **Archive integrity alone is not restore verification.** No live production SQL writes or migration occurred.

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

On `pracill`, Docker is reachable and the official Supabase CLI runs via `npx --yes supabase` (verified version `2.122.0`). A read-only `projects list` now succeeds and lists the expected project. No token or database URL was printed. The connected Supabase account and local CLI credentials remain separate authentication contexts.

### Completed backup export and local encryption (2026-10-24)

- Private backup ID: `pre0003-20261024-005819`. Stored under the owner's Windows `LOCALAPPDATA` profile with a restricted directory ACL; **not** uploaded to GitHub or this chat.
- The CLI exported the `public` application schema (`schema.sql`: 14,585 bytes), roles (`roles.sql`: 358 bytes), and `public` data (`data.sql`: 676,206 bytes) directly from the production project in read-only mode. This is **not** a full Supabase-managed Auth/Storage backup.
- Parsed the actual `COPY` sections without printing their rows: **370 procurement records = 250 official + 120 synthetic**; additional sections include ingestion runs, summaries, embeddings, logs and Alembic revision table.
- Created `production-pre0003.7z` (61,984 bytes) with encrypted headers and a freshly generated 288-bit passphrase. Verified the encrypted archive with `7z t`. Archive SHA-256: `1E7C4BBB126FD71DE961789DE6B54DB83DF4A7218C973FC4B1B4BA5EECD30711`.
- The passphrase is saved **only** as a Windows DPAPI `CurrentUser`-protected blob in `archive-password.dpapi`. The plaintext SQL exports were then removed. **Critical limitation:** DPAPI is bound to the current Windows profile/machine key. There is not yet a portable, separately stored recovery key or off-device copy. Do not treat this as disaster-recovery ready.
- Attempting to execute the SQL restore inside an isolated PostgreSQL 17 Docker container was blocked by the remote execution tool's safety checks. **No SQL restore was run**, and the container was stopped and removed. This is **not** evidence of a restore failure in the SQL files; it remains **untested**. See `backup-manifest.json` inside the owner's private backup folder for metadata and local artifact hashes.
- **STOP:** Production release still requires a successful, independently checked isolated restore, a portable recovery key kept securely outside the machine, and a protected off-device copy. Do not run the production Alembic migration until those gates are complete.

### Preview isolation

The protected Vercel Preview remains database-unready (readiness HTTP 503 and data endpoints HTTP 500) because there is no Preview-specific `DATABASE_URL`. No production URL was copied to Preview. The connected Neon account showed no matching procurement projects; querying Supabase development branches returned insufficient permission, so this does **not** prove that no branches exist. Use an explicitly approved, independently isolated Preview database rather than reusing production credentials.


## Free-tier Preview database decision — 2026-10-24

**No new infrastructure was created during this review.**

Supabase's current Free plan includes **two active Free projects total across qualifying organizations**, but **Supabase Branching/automatic PR preview branches are a Pro-plan feature**. A second, independent Free-plan Supabase project is therefore a possible zero-subscription-cost Preview environment **only if the account has a remaining free-project slot and the selected organization is itself on the Free plan**. Do not infer capacity from the project's own Free subscription or from the CLI returning a single visible project.

Before creating any project:
1. Verify available Free slots **across all applicable organizations**, confirm the target organization and check actual creation cost with the official Supabase cost-quote tool. Obtain explicit owner approval after showing the quoted price; never create a potentially billable project by assumption.
2. If an eligible $0 slot is available, name the new Preview project unambiguously, use a region near the existing app and **never clone production users, secrets, rows or storage** into it.
3. Apply exactly the checked-in Alembic migrations to an empty Preview database, then import **only** the committed synthetic sample. Confirm the deployed app's Preview-only connection role can query its tables under any project-specific automatic RLS enforcement.
4. Create **Preview-scoped only** environment variables in Vercel: a secret `DATABASE_URL` for that new database, `DATASET_MODE=synthetic`, `NEXT_PUBLIC_API_BASE_URL=/backend/api`, `ENABLE_LLM=false`, and `LOG_AI_QUERIES=false`. Never set a production secret in Preview, including through unscoped shared variables.
5. Redeploy **Preview only**, then verify `/backend/api/health/readiness` HTTP 200 with exactly **120 synthetic rows**, `/backend/api/dataset/status` reports synthetic, read/search/assistant mock paths work, and no official records are shown. Keep Preview behind deployment protection.
6. Monitor project status and Free limits; Free projects may **pause after inactivity**, so a Preview environment is not guaranteed to stay always-on.

If the Free allocation is exhausted or the quoted cost is not $0, **stop**. The fallback is a local PostgreSQL+Playwright integration rehearsal with clearly documented limitations, not reusing the production database, paying without approval, or presenting a build-only preview as runtime verified.

Sources:
- <https://supabase.com/docs/guides/platform/billing-on-supabase>
- <https://supabase.com/docs/guides/deployment>
- <https://supabase.com/docs/guides/platform/manage-your-usage/branching>
- <https://vercel.com/docs/environment-variables/manage-across-environments>

## Restore-test and recovery-key ownership

The application SQL archive is present, but a **successful isolated database restore has not been verified**. The archive uses Windows DPAPI for local password protection; a catastrophic loss of the workstation/profile may make the archive unusable, even if its encrypted bytes are copied elsewhere. Do not count a duplicate DPAPI-encrypted password file on another drive as a portable recovery key.

The owner must choose an appropriate long-term, independently recoverable secret-storage and off-device backup destination. Do not print or transmit the generated archive password in terminal transcripts, GitHub logs or ChatGPT. Once the owner has a portable recovery method, a separately authorized operator should follow the official Supabase backup/restore procedure in an isolated PostgreSQL 17 environment, validating **data, roles, schema, Alembic revision and row counts**, and record a success or failure independently. **Do not bypass remote-tool safety restrictions** to run a restore. Until then, Gate A stays blocked.
