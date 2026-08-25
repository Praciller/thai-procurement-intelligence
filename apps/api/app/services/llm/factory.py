import logging
import os

from app.config import Settings, get_settings
from app.services.llm.adapters import GeminiNativeProvider, OpenAICompatibleProvider
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.provider_config import ProviderConfig
from app.services.llm.router import ProviderEntry, ProviderRouter

logger = logging.getLogger(__name__)


def _provider_configs(settings: Settings) -> dict[str, ProviderConfig]:
    timeout = settings.llm_timeout_seconds
    retries = settings.llm_max_retries
    return {
        "gemini": ProviderConfig(
            name="gemini",
            api_style="gemini_native",
            base_url=settings.gemini_base_url,
            api_key_env="GEMINI_API_KEY",
            model=settings.gemini_model,
            timeout=timeout,
            max_retries=retries,
            enabled=True,
            automatic_fallback_allowed=True,
            deterministic_evaluation_allowed=True,
        ),
        "groq": ProviderConfig(
            name="groq",
            api_style="openai_compatible",
            base_url=settings.groq_base_url,
            api_key_env="GROQ_API_KEY",
            model=settings.groq_model,
            timeout=timeout,
            max_retries=retries,
            enabled=True,
            automatic_fallback_allowed=True,
            deterministic_evaluation_allowed=True,
        ),
        "cerebras": ProviderConfig(
            name="cerebras",
            api_style="openai_compatible",
            base_url=settings.cerebras_base_url,
            api_key_env="CEREBRAS_API_KEY",
            model=settings.cerebras_model,
            timeout=timeout,
            max_retries=retries,
            # The 2026-08-25 smoke reached the API but returned HTTP 402;
            # keep it out of the active chain until account capacity is proven.
            enabled=False,
            automatic_fallback_allowed=False,
            deterministic_evaluation_allowed=True,
        ),
        "openrouter": ProviderConfig(
            name="openrouter",
            api_style="openai_compatible",
            base_url=settings.openrouter_base_url,
            api_key_env="OPENROUTER_API_KEY",
            model=settings.openrouter_model,
            timeout=timeout,
            max_retries=retries,
            enabled=True,
            automatic_fallback_allowed=True,
            deterministic_evaluation_allowed=False,
        ),
        "okmd": ProviderConfig(
            name="okmd",
            api_style="openai_compatible",
            base_url=settings.okmd_base_url,
            api_key_env="OKMD_API_KEY",
            model=settings.okmd_model,
            timeout=timeout,
            max_retries=retries,
            enabled=settings.enable_okmd_fallback,
            automatic_fallback_allowed=settings.enable_okmd_fallback,
            deterministic_evaluation_allowed=True,
        ),
        "thaillm": ProviderConfig(
            name="thaillm",
            api_style="openai_compatible",
            base_url=settings.thaillm_base_url,
            api_key_env="THAILLM_API_KEY",
            model=settings.thaillm_model,
            timeout=timeout,
            max_retries=retries,
            enabled=settings.enable_thaillm_fallback,
            automatic_fallback_allowed=settings.enable_thaillm_fallback,
            deterministic_evaluation_allowed=True,
        ),
    }


def _requested_provider_names(settings: Settings) -> list[str]:
    selected = (settings.llm_provider or "").strip().lower()
    if selected and selected != "auto":
        names = [selected]
    else:
        names = [name.strip().lower() for name in settings.llm_provider_chain.split(",")]
    return [name for name in names if name]


def _mock_entry() -> ProviderEntry:
    return ProviderEntry(
        config=ProviderConfig(
            name="mock",
            api_style="mock",
            base_url=None,
            api_key_env=None,
            model="deterministic-mock-v1",
            timeout=0,
            max_retries=0,
            enabled=True,
            automatic_fallback_allowed=True,
            deterministic_evaluation_allowed=True,
        ),
        provider=MockLLMProvider(),
    )


def get_llm_provider(
    settings: Settings | None = None,
    *,
    deterministic_evaluation: bool = False,
) -> LLMProvider:
    current_settings = settings or get_settings()
    if not current_settings.enable_llm:
        return MockLLMProvider()

    configs = _provider_configs(current_settings)
    entries: list[ProviderEntry] = []
    for name in _requested_provider_names(current_settings):
        if name == "mock":
            entries.append(_mock_entry())
            continue

        config = configs.get(name)
        if config is None or not config.enabled:
            logger.debug("LLM provider skipped provider=%s reason=disabled_or_unknown", name)
            continue

        api_key = os.getenv(config.api_key_env or "")
        if not api_key:
            logger.debug("LLM provider skipped provider=%s reason=missing_credential", name)
            continue

        if config.api_style == "gemini_native":
            provider: LLMProvider = GeminiNativeProvider(config, api_key)
        elif config.api_style == "openai_compatible":
            provider = OpenAICompatibleProvider(config, api_key)
        else:
            logger.debug("LLM provider skipped provider=%s reason=unsupported_api_style", name)
            continue
        entries.append(ProviderEntry(config=config, provider=provider))

    if not any(entry.config.name == "mock" for entry in entries):
        entries.append(_mock_entry())

    return ProviderRouter(tuple(entries), deterministic_evaluation=deterministic_evaluation)
