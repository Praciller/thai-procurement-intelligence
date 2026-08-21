# Tradeoffs

- The project uses deterministic local embeddings instead of a paid embedding API. This demonstrates semantic/hybrid retrieval flow without external inference cost.
- PostgreSQL is the intended runtime database. SQLite support exists to make tests and local smoke checks cheap.
- Excel import is declared as an extension point, while CSV import is the implemented path.
- Public summaries and cited answers are deterministic and evidence-bound. This favors reproducibility and inspectability over open-ended generation.
- The sample dataset is synthetic. It proves system behavior but should not be used for real public-sector analysis.
