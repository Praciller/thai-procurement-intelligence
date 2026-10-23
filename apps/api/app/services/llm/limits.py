"""Pre-inference input bounds for optional external provider chains."""

from fastapi import HTTPException

from app.config import Settings
from app.services.llm.base import LLMProvider

MAX_EXTERNAL_LLM_INPUT_CHARACTERS = 24_000


def enforce_external_prompt_limit(
    provider: LLMProvider,
    settings: Settings,
    messages: list[dict[str, str]],
) -> None:
    """Reject oversized external-capable payloads before reserving a DB permit.

    Size applies to assembled question/record context, not just the incoming
    question. Use may_call_external to include mock-first fallback chains.
    Offline-only inference is unaffected.
    """
    if not settings.enable_llm or not provider.may_call_external:
        return
    characters = sum(len(message.get("content", "")) for message in messages)
    if characters > MAX_EXTERNAL_LLM_INPUT_CHARACTERS:
        raise HTTPException(
            status_code=413,
            detail="LLM input exceeds the configured size limit",
        )
