# Synthetic Dataset

`data/sample/procurement_sample.csv` contains 120 generated demonstration records. It is not copied, sampled, or inferred from official Thai procurement records.

## Purpose and Limits

The dataset demonstrates ingestion, validation, normalization, deduplication, filtering, analytics, deterministic embeddings, and evidence-limited Q&A. It does not support claims about real agencies, vendors, contracts, awards, budgets, geography, or public spending.

Names deliberately use `Sample` identifiers. Dates, amounts, descriptions, URLs, and relationships are generated for product testing. No field should be treated as official evidence.

## Data Dictionary

| Field | Type | Constraint / assumption |
| --- | --- | --- |
| `source_record_id` | string | Stable synthetic identifier; unique within source |
| `project_name` | string | Required generated project title |
| `agency_name` | string | Generated name prefixed with `Sample` |
| `province` | string | Normalized demonstration category |
| `procurement_method` | string | Demonstration procurement method |
| `procurement_category` | string | Demonstration analytics category |
| `budget_amount` | decimal | Non-negative generated THB amount |
| `winning_amount` | decimal | Generated THB amount; not a real award |
| `winner_name` | string | Generated name prefixed with `Sample` |
| `announcement_date` | date | Generated ISO date |
| `contract_date` | date | Generated ISO date |
| `source_url` | string | Placeholder provenance field; not proof of an official record |
| `raw_text` | string | Generated descriptive text |

Regenerate with `npm run sample:data`, then verify the diff before committing. Generated exports and local evidence belong under ignored directories, not in the public repository.
