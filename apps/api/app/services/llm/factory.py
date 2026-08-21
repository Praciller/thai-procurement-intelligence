from app.config import Settings, get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    _ = settings or get_settings()
    return MockLLMProvider()
