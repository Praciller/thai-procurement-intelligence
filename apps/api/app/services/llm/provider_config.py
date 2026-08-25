from dataclasses import dataclass
from typing import Literal


ApiStyle = Literal["gemini_native", "openai_compatible", "mock"]


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_style: ApiStyle
    base_url: str | None
    api_key_env: str | None
    model: str
    timeout: float
    max_retries: int
    enabled: bool
    automatic_fallback_allowed: bool
    deterministic_evaluation_allowed: bool
