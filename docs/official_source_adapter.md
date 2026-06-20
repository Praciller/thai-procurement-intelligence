# Official Source Adapter Design

No official Thai procurement source is enabled or claimed by this repository.

The existing `DataSource.rows()` boundary accepts canonicalizable dictionaries. `CsvDataSource` and `OpenApiDataSource` feed the same validation, normalization, deduplication, ingestion-run, and error-reporting path. Future Excel support is an extension point, not an implemented claim.

An official adapter must:

- use a documented public source with approved terms; no browser scraping or undocumented endpoint
- emit stable source IDs and record-level source URLs where available
- attach a unique source name and preserve raw source fields needed for audit
- map CSV, JSON, or future Excel fields through a reviewed versioned mapping
- reject invalid required fields and record row-level errors
- support idempotent re-import and documented rollback
- pass fixture-only tests without network access

Keep adapters disabled by default until the provenance checklist in [data_provenance.md](data_provenance.md) is approved. Network smoke tests, if later added, must be opt-in and must not run in default CI.
