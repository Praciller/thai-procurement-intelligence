# Official bounded snapshot

Snapshot ID: `dga-egp-contract-2568-250`  
Retrieved: 2026-06-21T14:02:45.343910Z  
Coverage: 2024-10-04 through 2025-09-29  
Records: 250  
SHA-256: `413f70c0ef17c17233b99aa42a7f1e25284644948c37bd109c21e9cc0678618b`

The snapshot is the first 250 unique project IDs from resource part 10 of DGA's fiscal-year 2568 EGP contract dataset. It is a deterministic portfolio fixture, not a complete or representative sample of Thai procurement.

Reacquire it with one bounded official download request:

```powershell
apps/api/.venv/Scripts/python.exe scripts/acquire_official_snapshot.py `
  --output data/official/raw/dga-egp-contract-2568-250.csv `
  --metadata data/official/metadata/dga-egp-contract-2568-250.json
```

The command restricts the host to `data.go.th`, sets a 60-second timeout, reads at most 1 MiB, validates content type, retains only approved fields, excludes supplier/legal identifiers, and records upstream headers and the generated checksum.

Import after applying migrations:

```powershell
$env:DATASET_MODE="official_snapshot"
cd apps/api
uv run alembic upgrade head
uv run python -m app.jobs.import_official_snapshot `
  --file ../../data/official/raw/dga-egp-contract-2568-250.csv `
  --metadata ../../data/official/metadata/dga-egp-contract-2568-250.json
```

A second import inserts zero rows and reports 250 unchanged rows.
