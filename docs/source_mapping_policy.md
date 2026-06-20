# Source Mapping Policy

Each external source needs a reviewed mapping from its versioned schema to the canonical fields in [synthetic_dataset.md](synthetic_dataset.md).

The mapping record must include publisher, source URL, terms/license decision, source schema version, canonical field, source field, transformation, required/null behavior, validation rule, provenance field, and reviewer/date.

Mapping tests use committed non-sensitive fixtures and no network access. They must cover required-field failure, date and decimal normalization, source ID deduplication, unknown fields, and preservation of source references.

Changes to an approved source schema stop ingestion until the mapping and fixtures are reviewed. Failed imports remain visible through ingestion-run/error records. Re-imports must be idempotent by source name and source record ID; rollback is performed from a database backup or by a reviewed run-scoped deletion, not by silently overwriting provenance.
