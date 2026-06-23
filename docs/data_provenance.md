# Data Provenance Policy

## Current Status

The project supports two isolated modes:

- `synthetic`: the default 120-record deterministic demo.
- `official_snapshot`: a 250-record bounded DGA/data.go.th snapshot retrieved on 2026-06-21.

Official records retain source record ID, dataset URL, snapshot ID, retrieval/source update timestamps, license, snapshot checksum, mapping version, and `is_synthetic=false`. Search, analytics, export, details, and assistant retrieval filter by the active mode.

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

The approved snapshot and its evidence reports are committed under the restrictions in [official_source_review.md](official_source_review.md). Database dumps and other source files remain local unless separately approved.
