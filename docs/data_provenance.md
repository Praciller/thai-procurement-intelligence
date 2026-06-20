# Data Provenance Policy

## Current Status

All committed demo records are synthetic. The application may ingest user-supplied CSV or JSON, but that capability does not make a source official or approved.

## Approval Gate for Official Data

Before any dataset is described as official, every item below must be reviewed and recorded:

1. Publisher identity and canonical source URL.
2. License, terms, access method, privacy, and permitted reuse.
3. Versioned source-to-canonical schema mapping.
4. Raw-file checksum and retrieval timestamp.
5. Timestamped ingestion run ID, importer version, and source label.
6. Validation errors, rejected-row counts, and corrective decisions.
7. Stable source record ID and record-level source URL where available.
8. Deduplication and re-import behavior.
9. Reviewer approval for UI labels and portfolio claims.

Records must be labeled as `synthetic`, `sampled`, or `official`; these labels are not interchangeable. A sample from an official source must still disclose sampling and cannot represent source-wide statistics.

Raw source files, database dumps, generated exports, and evidence reports remain local unless their license, privacy, size, and purpose are explicitly approved.
