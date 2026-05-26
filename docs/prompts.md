# AI Prompts

Prompt templates live in `apps/api/app/prompts/`.

Rules used across providers:

- Use only provided procurement fields and raw text.
- Do not invent missing facts.
- Say when information is not available.
- Cite record IDs or project names in assistant answers.
- Prefer Thai output unless the question is in English.

LLM providers are optional. With `ENABLE_LLM=false`, core search, dashboard, details, ingestion, export, and evidence retrieval still work.

