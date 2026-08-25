import asyncio
import logging
from collections.abc import Iterable
from decimal import Decimal

import pytest

from app.config import Settings
from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider
from app.services.llm.errors import ProviderError, ProviderFailureCategory
from app.services.llm.factory import get_llm_provider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.provider_config import ProviderConfig
from app.services.llm.router import ProviderEntry, ProviderRouter


class ScriptedProvider(LLMProvider):
    def __init__(self, name: str, outcomes: Iterable[str | Exception]) -> None:
        self.provider_name = name
        self.model_name = f"{name}-test-model"
        self.outcomes = list(outcomes)
        self.calls = 0

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return self._next()

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        return self._next()

    def _next(self) -> str:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _config(
    name: str,
    *,
    max_retries: int = 0,
    enabled: bool = True,
    automatic: bool = True,
    deterministic: bool = True,
) -> ProviderConfig:
    return ProviderConfig(
        name=name,
        api_style="mock",
        base_url=None,
        api_key_env=None,
        model=f"{name}-model",
        timeout=1,
        max_retries=max_retries,
        enabled=enabled,
        automatic_fallback_allowed=automatic,
        deterministic_evaluation_allowed=deterministic,
    )


def _entry(
    name: str,
    outcomes: Iterable[str | Exception],
    *,
    max_retries: int = 0,
    enabled: bool = True,
    automatic: bool = True,
    deterministic: bool = True,
) -> tuple[ProviderEntry, ScriptedProvider]:
    provider = ScriptedProvider(name, outcomes)
    return (
        ProviderEntry(
            config=_config(
                name,
                max_retries=max_retries,
                enabled=enabled,
                automatic=automatic,
                deterministic=deterministic,
            ),
            provider=provider,
        ),
        provider,
    )


def _error(category: ProviderFailureCategory, *, status_code: int | None = None) -> ProviderError:
    return ProviderError("scripted", category, model_name="scripted-model", status_code=status_code)


def _record() -> ProcurementRecord:
    return ProcurementRecord(
        id="record-1",
        source_name="fixture",
        dataset_type="synthetic",
        source_record_id="FIXTURE-1",
        content_hash="a" * 64,
        project_name="Public computer procurement",
        agency_name="Fixture agency",
        budget_amount=Decimal("100"),
        raw_text="Public procurement evidence",
        normalized_text="Public procurement evidence",
        is_synthetic=True,
    )


def _answer(router: ProviderRouter, question: str = "public project") -> str:
    return asyncio.run(router.answer_question(question, [_record()]))


def test_primary_success_and_configured_ordering():
    first_entry, first = _entry("first", ["primary answer"])
    second_entry, second = _entry("second", ["fallback answer"])

    router = ProviderRouter([first_entry, second_entry])

    assert _answer(router) == "primary answer"
    assert router.provider_names == ("first", "second")
    assert first.calls == 1
    assert second.calls == 0
    assert router.provider_name == "first"


def test_timeout_retries_once_then_falls_back():
    first_entry, first = _entry(
        "timeout",
        [_error(ProviderFailureCategory.TIMEOUT), _error(ProviderFailureCategory.TIMEOUT)],
        max_retries=1,
    )
    second_entry, second = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([first_entry, second_entry])) == "backup answer"
    assert first.calls == 2
    assert second.calls == 1


def test_rate_limit_falls_back_without_unbounded_retry():
    first_entry, first = _entry(
        "limited",
        [_error(ProviderFailureCategory.RATE_LIMIT)],
        max_retries=3,
    )
    second_entry, _ = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([first_entry, second_entry])) == "backup answer"
    assert first.calls == 1


def test_authentication_error_does_not_retry_but_can_fallback():
    first_entry, first = _entry("bad-auth", [_error(ProviderFailureCategory.AUTH_ERROR, status_code=401)], max_retries=3)
    second_entry, _ = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([first_entry, second_entry])) == "backup answer"
    assert first.calls == 1


def test_transient_server_error_has_bounded_retry():
    first_entry, first = _entry(
        "server",
        [_error(ProviderFailureCategory.TRANSIENT_5XX, status_code=503), "recovered"],
        max_retries=1,
    )

    assert _answer(ProviderRouter([first_entry])) == "recovered"
    assert first.calls == 2


def test_unknown_error_gets_only_one_retry():
    first_entry, first = _entry(
        "unknown",
        [_error(ProviderFailureCategory.UNKNOWN), _error(ProviderFailureCategory.UNKNOWN)],
        max_retries=3,
    )
    second_entry, _ = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([first_entry, second_entry])) == "backup answer"
    assert first.calls == 2


def test_bad_request_is_not_retried_or_silently_fallback():
    first_entry, first = _entry("invalid", [_error(ProviderFailureCategory.BAD_REQUEST, status_code=400)], max_retries=3)
    second_entry, second = _entry("backup", ["must not be used"])

    with pytest.raises(ProviderError) as error:
        _answer(ProviderRouter([first_entry, second_entry]))

    assert error.value.category == ProviderFailureCategory.BAD_REQUEST
    assert first.calls == 1
    assert second.calls == 0


def test_network_failure_falls_back():
    first_entry, _ = _entry("offline", [_error(ProviderFailureCategory.NETWORK_ERROR)])
    second_entry, _ = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([first_entry, second_entry])) == "backup answer"


def test_disabled_provider_is_skipped():
    disabled_entry, disabled = _entry("disabled", ["must not be used"], enabled=False)
    backup_entry, _ = _entry("backup", ["backup answer"])

    assert _answer(ProviderRouter([disabled_entry, backup_entry])) == "backup answer"
    assert disabled.calls == 0


def test_all_unavailable_providers_end_at_deterministic_mock():
    failed_entry, _ = _entry("failed", [_error(ProviderFailureCategory.NETWORK_ERROR)])
    mock = MockLLMProvider()
    mock_entry = ProviderEntry(_config("mock"), mock)

    answer = _answer(ProviderRouter([failed_entry, mock_entry]))

    assert "Evidence:" in answer


def test_missing_credentials_and_default_exclusions(monkeypatch: pytest.MonkeyPatch):
    for env_name in (
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "CEREBRAS_API_KEY",
        "OPENROUTER_API_KEY",
        "OKMD_API_KEY",
        "THAILLM_API_KEY",
    ):
        monkeypatch.delenv(env_name, raising=False)

    settings = Settings(
        _env_file=None,
        enable_llm=True,
        llm_provider_chain="gemini,groq,openrouter,okmd,thaillm,mock",
    )
    provider = get_llm_provider(settings)

    assert provider.provider_names == ("mock",)


def test_provider_order_is_preserved_when_credentials_are_present(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only")
    monkeypatch.setenv("GROQ_API_KEY", "test-only")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")
    settings = Settings(_env_file=None, enable_llm=True, llm_provider_chain="groq,gemini,openrouter,mock")

    provider = get_llm_provider(settings)

    assert provider.provider_names == ("groq", "gemini", "openrouter", "mock")


def test_openrouter_is_blocked_from_deterministic_evaluation():
    openrouter_entry, openrouter = _entry("openrouter", ["nondeterministic"], deterministic=False)
    mock_entry, _ = _entry("mock", ["deterministic answer"])

    router = ProviderRouter([openrouter_entry, mock_entry], deterministic_evaluation=True)

    assert _answer(router) == "deterministic answer"
    assert openrouter.calls == 0


def test_thaillm_is_excluded_for_private_request():
    thaillm_entry, thaillm = _entry("thaillm", ["private answer"])
    mock_entry, _ = _entry("mock", ["public fallback"])

    assert _answer(ProviderRouter([thaillm_entry, mock_entry]), "confidential project") == "public fallback"
    assert thaillm.calls == 0


def test_thaillm_and_okmd_are_not_default_automatic_fallbacks(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("THAILLM_API_KEY", "test-only")
    monkeypatch.setenv("OKMD_API_KEY", "test-only")
    settings = Settings(_env_file=None, enable_llm=True, llm_provider_chain="thaillm,okmd,mock")

    provider = get_llm_provider(settings)

    assert provider.provider_names == ("mock",)


def test_provider_failure_logs_do_not_contain_credentials(caplog: pytest.LogCaptureFixture):
    entry, _ = _entry("logged", [_error(ProviderFailureCategory.AUTH_ERROR, status_code=401)])
    router = ProviderRouter([entry])

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ProviderError):
            _answer(router)

    assert "api_key" not in caplog.text
    assert "Authorization" not in caplog.text
    assert "auth_error" in caplog.text


def test_generated_summary_respects_existing_provider_contract():
    record = _record()
    mock = MockLLMProvider()

    summary = asyncio.run(mock.generate_summary(record))

    assert "Project purpose: Public computer procurement" in summary


def test_cited_question_answer_preserves_grounding_behavior():
    record = _record()
    mock = MockLLMProvider()

    answer = asyncio.run(mock.answer_question("which project?", [record]))

    assert "Public computer procurement" in answer
    assert "Evidence:" in answer
