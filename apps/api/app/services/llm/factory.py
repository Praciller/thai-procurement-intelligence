from app.config import Settings, get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openrouter import OpenRouterProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    if not settings.enable_llm:
        return MockLLMProvider()
    if settings.llm_provider == "gemini":
        return GeminiProvider(settings)
    if settings.llm_provider == "openrouter":
        return OpenRouterProvider(settings)
    return MockLLMProvider()

