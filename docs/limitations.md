# Limitations

- The official snapshot contains 250 records from one resource part and is not statistically representative.
- The source may change after the 2026-06-21 retrieval date; the UI reports snapshot freshness rather than implying live data.
- The portal states `Creative Commons Attributions` but supplies no license version or license URL.
- Supplier names and legal identifiers are deliberately excluded.
- Contract dates and source fields after province are excluded because upstream row alignment is not consistently reliable.
- Retrieval evaluation uses eight frozen judged queries on the bounded 250-record snapshot; it is useful regression evidence, not production-scale or population-representative evidence.
- Deterministic hash embeddings provide a free local retrieval baseline, not a claim of state-of-the-art semantic quality; on the current judged set hybrid ranking does not improve the aggregate relevance metrics over keyword ranking and returns five results for the negative control.
- Generated summaries are labeled, evidence-constrained, and require human verification against the official source.
- Public procurement data is not proof of fraud, corruption, misconduct, or suspicious behavior.
- The optional hosted deployment was verified on 2026-08-24 in `official_snapshot` mode with 250 records; hosted state must be re-verified after future deployments or database lifecycle events.
