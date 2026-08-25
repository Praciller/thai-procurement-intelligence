# Multi-provider LLM routing

LLM calls are opt-in. The default `ENABLE_LLM=false` keeps local development, tests, and the deterministic mock fallback offline. No provider credential belongs in the repository or in logs.

## Verified provider matrix

The implementation was checked with presence-only credential handling and safe status output on 2026-08-25:

| Provider | API style | Result | Runtime policy |
| --- | --- | --- | --- |
| Gemini | Native `generateContent` | Chat passed with `gemini-2.5-flash` | Active default primary |
| Groq | OpenAI-compatible | Chat passed with `openai/gpt-oss-20b` | Active default fallback |
| Cerebras | OpenAI-compatible | HTTP 402 quota/payment response | Excluded until account capacity is available |
| OpenRouter | OpenAI-compatible | `openrouter/free` returned a dynamic free model | Active fallback only; not deterministic evaluation |
| OKMD | OpenAI-compatible | Chat passed with `gemini-2.5-flash-lite` | Development/evaluation only; explicit opt-in |
| ThaiLLM | OpenAI-compatible | Chat passed with `Pathumma-ThaiLLM-qwen3-8b-think-3.0.0` | Explicit opt-in and public/demo data only |

The active default chain is `gemini,groq,openrouter,mock`. The verified provider matrix is evidence for local integration only; the production chain was not deployed by this change.

## Configuration

Set `ENABLE_LLM=true` and provide only the credentials for the providers intentionally enabled. `LLM_PROVIDER_CHAIN` controls order. A missing credential is skipped without logging its value. The chain always ends with the deterministic local `mock` provider.

Gemini uses its native endpoint and `x-goog-api-key`. Groq, Cerebras, OpenRouter, OKMD, and ThaiLLM use the OpenAI-compatible adapter. Timeouts and retry counts are bounded by `LLM_TIMEOUT_SECONDS` and `LLM_MAX_RETRIES`.

`OKMD` requires `ENABLE_OKMD_FALLBACK=true` and is not part of the default automatic chain. `ThaiLLM` requires `ENABLE_THAILLM_FALLBACK=true`; requests containing privacy markers such as `private`, `confidential`, `personal`, `secret`, `ส่วนบุคคล`, or `ข้อมูลลับ` are kept off that provider.

## Fallback and evaluation rules

Authentication and malformed-request failures are not blindly retried. Rate limits, quota responses, timeouts, network failures, and transient 5xx responses receive bounded retry/fallback handling. Content-policy failures are surfaced rather than silently bypassed.

Provider logs contain only provider, model, operation, attempt, duration, result, fallback source, category, and status class. They never contain API keys, authorization headers, prompts, or full model responses.

OpenRouter's `openrouter/free` selection is intentionally nondeterministic because the service may select different free models. The router excludes it from deterministic judged evaluation. Evaluation should use the mock provider or a fixed, approved provider configuration and record its provider/model explicitly.

The deterministic hash embedding used elsewhere in this project remains a zero-cost architecture/demo baseline; it is not production semantic retrieval and is unrelated to provider selection.
