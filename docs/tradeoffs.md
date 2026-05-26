# Tradeoffs

- The MVP includes deterministic local embeddings instead of relying on a paid embedding API. This demonstrates semantic/hybrid retrieval flow without cost.
- PostgreSQL is the intended runtime database. SQLite support exists to make tests and local smoke checks cheap.
- Excel import is declared as an extension point, but CSV import is the implemented MVP path.
- LLM providers are implemented for Gemini and OpenRouter, but local demos default to a mock provider so the app works without private keys.
- The sample dataset is synthetic. It proves system behavior but should not be used for real public-sector analysis.

