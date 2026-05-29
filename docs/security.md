# Security And Secret Rotation

Do not commit provider keys, database URLs, or GitHub tokens.

The current deployment stores runtime secrets in Vercel environment variables. If a key is pasted into chat, terminal logs, screenshots, or issue text, treat it as exposed.

## Rotation Checklist

1. Revoke the exposed GitHub token.
2. Create a new GitHub token with the smallest repo scope needed.
3. Revoke the exposed OpenRouter key.
4. Create a new OpenRouter key and update `OPENROUTER_API_KEY` in Vercel Production.
5. Revoke the exposed Gemini key if it will be used.
6. Create a new Gemini key only if `LLM_PROVIDER=gemini` is needed.
7. Redeploy Vercel after changing runtime environment variables.
8. Run production smoke checks:

```bash
curl https://thai-procurement-intelligence.vercel.app/backend/api/health
curl https://thai-procurement-intelligence.vercel.app/backend/api/health/readiness
curl "https://thai-procurement-intelligence.vercel.app/backend/api/records?page_size=1"
```

## Current Public Client Variables

These are intentionally public because browser code can read any `NEXT_PUBLIC_` value:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SITE_URL`

Never put private API keys in `NEXT_PUBLIC_` variables.
