# Data Source

The repository includes `data/sample/procurement_sample.csv` with 120 synthetic sample records. All agencies and vendors use obvious sample names. The UI labels this as demo data.

The ingestion layer accepts CSV rows with canonical fields or common aliases:

- `project_name`
- `agency_name`
- `province`
- `procurement_method`
- `procurement_category`
- `budget_amount`
- `winning_amount`
- `winner_name`
- `announcement_date`
- `contract_date`
- `source_url`
- `raw_text`

Future public sources can be added through `app/data_sources/` without changing API routes.

## Generic JSON Source Import

For a public JSON endpoint that returns either a list of records or an object with an `items` array, use:

```bash
cd apps/api
uv run python -m app.jobs.fetch_source --url "https://example.test/procurement.json" --source-name public_api
```

The importer reuses the same alias mapping as CSV ingestion, so source records should map to the canonical fields above or common aliases such as `project`, `agency`, `budget`, `announce_date`, `url`, and `details`.

Before replacing the sample dataset with a real Thai procurement source, confirm:

- source terms allow reuse in this demo
- record identifiers are stable enough for deduplication
- field mapping has been reviewed against real payload examples
- `source_url` or equivalent provenance is preserved per record
- the UI copy no longer describes records as synthetic sample data
