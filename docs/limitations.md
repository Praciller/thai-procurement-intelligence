# Limitations

- The official snapshot contains 250 records from one resource part and is not statistically representative.
- The source may change after the 2026-06-21 retrieval date; the UI reports snapshot freshness rather than implying live data.
- The portal states `Creative Commons Attributions` but supplies no license version or license URL.
- Supplier names and legal identifiers are deliberately excluded.
- Contract dates and source fields after province are excluded because upstream row alignment is not consistently reliable.
- Keyword and hybrid evaluation uses four labeled queries on an in-memory bounded fixture; it is not production-scale evidence.
- Deterministic hash embeddings provide a free local retrieval baseline, not a claim of state-of-the-art semantic quality.
- Generated summaries are labeled, evidence-constrained, and require human verification against the official source.
- Public procurement data is not proof of fraud, corruption, misconduct, or suspicious behavior.
- The optional hosted deployment remains synthetic until it is explicitly migrated, configured, and verified.
