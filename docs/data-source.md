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

