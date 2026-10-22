from fastapi import HTTPException, Request

from app.services.llm.base import LLMProvider
from app.services.rate_limit import claim_external_llm_request


MAX_LLM_INPUT_CHARACTERS = 24_000


def enforce_external_provider_limits(provider: LLMProvider, request: Request, messages: list[dict[str, str]]) -> None:
    if not provider.is_external:
        return

    input_size = sum(len(message.get("content", "")) for message in messages)
    if input_size > MAX_LLM_INPUT_CHARACTERS:
        raise HTTPException(status_code=413, detail="LLM input exceeds the configured size limit")

    client_ip = request.client.host if request.client else "unknown"
    retry_after = claim_external_llm_request(client_ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="External LLM request limit reached. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
