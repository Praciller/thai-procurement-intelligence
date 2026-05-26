# Domain Glossary

Procurement record: one normalized public procurement notice or contract-like row imported from sample or public source data.

Source record: the original upstream row before normalization. It may have a source ID, URL, raw text, and provider-specific column names.

Ingestion run: one import attempt against a CSV, upload, or API source, including inserted, updated, skipped, and failed row counters.

AI summary: cached generated text derived only from a procurement record's structured fields and raw text.

Evidence citation: a procurement record returned with an assistant answer to show which records support the response.

Demo dataset: synthetic sample records with sample agency and vendor names. It is not real procurement evidence.

