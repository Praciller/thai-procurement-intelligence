# Official snapshot data quality

Run from the repository root:

```powershell
$env:PYTHONPATH="apps/api"
apps/api/.venv/Scripts/python.exe -m app.jobs.evaluate_official_snapshot
```

The command verifies the SHA-256 checksum, maps every row, applies required-field, amount, date, official-domain, provenance, and duplicate checks, then rewrites deterministic reports under `reports/official_snapshot/`.

Measured on 2026-06-22:

| Metric | Result |
| --- | ---: |
| Raw records | 250 |
| Valid records | 250 |
| Rejected records | 0 |
| Duplicate source keys | 0 |
| Warning records | 0 |
| Ingestion success | 100% |
| Coverage | 2024-10-04 to 2025-09-29 |

The completeness artifact reports each mapped field independently. Contract dates are intentionally unavailable because the approved bounded subset excludes trailing source columns whose row alignment is unreliable. Empty values are not synthesized.

When a hosted deployment cannot read the quality artifact, `/api/dataset/status` reconstructs limited status information from persisted records. The fallback reports `checksum_verified=false` because matching checksum strings stored in the database do **not** prove that the original source file bytes were verified. The separate `stored_provenance_consistent` flag describes only agreement between saved checksum fields. Run `app.jobs.evaluate_official_snapshot` against the original checked-in CSV to verify source bytes; do not present the fallback as an equivalent audit.
