from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from time import monotonic

from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider
from app.services.llm.errors import ProviderError, ProviderFailureCategory, status_class
from app.services.llm.provider_config import ProviderConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProviderEntry:
    config: ProviderConfig
    provider: LLMProvider


_PRIVATE_MARKERS = re.compile(r"private|confidential|personal|secret|ส่วนบุคคล|ข้อมูลลับ|ความลับ", re.IGNORECASE)
_NO_FALLBACK = {ProviderFailureCategory.BAD_REQUEST, ProviderFailureCategory.CONTENT_POLICY}


class ProviderRouter(LLMProvider):
    def __init__(self, entries: Sequence[ProviderEntry], *, deterministic_evaluation: bool = False) -> None:
        self.entries = tuple(entries)
        self.deterministic_evaluation = deterministic_evaluation
        self.provider_name = "router"
        self.model_name = "fallback"

    @property
    def provider_names(self) -> tuple[str, ...]:
        return tuple(entry.config.name for entry in self.entries)

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return await self._run(
            operation="generate_summary",
            call=lambda provider: provider.generate_summary(record),
            question="",
            records=[record],
        )

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        return await self._run(
            operation="answer_question",
            call=lambda provider: provider.answer_question(question, records),
            question=question,
            records=records,
        )

    async def _run(
        self,
        *,
        operation: str,
        call: Callable[[LLMProvider], Awaitable[str]],
        question: str,
        records: list[ProcurementRecord],
    ) -> str:
        fallback_from: str | None = None
        last_error: ProviderError | None = None
        for entry in self.entries:
            config = entry.config
            if not config.enabled or not config.automatic_fallback_allowed:
                continue
            if self.deterministic_evaluation and not config.deterministic_evaluation_allowed:
                logger.info("llm_provider_skipped provider=%s reason=deterministic_evaluation", config.name)
                continue
            if config.name == "thaillm" and not _thai_request_is_eligible(question, records):
                logger.info("llm_provider_skipped provider=%s reason=privacy_policy", config.name)
                continue

            max_attempts = 1 + min(max(0, config.max_retries), 3)
            for attempt in range(1, max_attempts + 1):
                started = monotonic()
                try:
                    answer = await call(entry.provider)
                except ProviderError as exc:
                    last_error = exc
                    duration_ms = int((monotonic() - started) * 1000)
                    logger.warning(
                        "llm_provider_failure provider=%s model=%s operation=%s attempt=%d duration_ms=%d "
                        "result=failure category=%s fallback_reason=%s status_class=%s fallback_from=%s",
                        config.name,
                        entry.provider.model_name,
                        operation,
                        attempt,
                        duration_ms,
                        exc.category.value,
                        exc.category.value,
                        status_class(exc.status_code),
                        fallback_from,
                    )
                    if not _can_retry(exc.category, attempt, max_attempts):
                        break
                    await asyncio.sleep(0)
                    continue
                except (asyncio.TimeoutError, TimeoutError):
                    last_error = ProviderError(config.name, ProviderFailureCategory.TIMEOUT, model_name=entry.provider.model_name)
                    logger.warning(
                        "llm_provider_failure provider=%s model=%s operation=%s attempt=%d duration_ms=%d "
                        "result=failure category=%s fallback_reason=%s status_class=none fallback_from=%s",
                        config.name,
                        entry.provider.model_name,
                        operation,
                        attempt,
                        int((monotonic() - started) * 1000),
                        ProviderFailureCategory.TIMEOUT.value,
                        ProviderFailureCategory.TIMEOUT.value,
                        fallback_from,
                    )
                    if attempt < min(max_attempts, 2):
                        await asyncio.sleep(0)
                        continue
                    break
                except Exception:
                    last_error = ProviderError(config.name, ProviderFailureCategory.UNKNOWN, model_name=entry.provider.model_name)
                    logger.warning(
                        "llm_provider_failure provider=%s model=%s operation=%s attempt=%d duration_ms=%d "
                        "result=failure category=%s fallback_reason=%s status_class=none fallback_from=%s",
                        config.name,
                        entry.provider.model_name,
                        operation,
                        attempt,
                        int((monotonic() - started) * 1000),
                        ProviderFailureCategory.UNKNOWN.value,
                        ProviderFailureCategory.UNKNOWN.value,
                        fallback_from,
                    )
                    if attempt < min(max_attempts, 2):
                        await asyncio.sleep(0)
                        continue
                    break
                else:
                    self.provider_name = entry.provider.provider_name
                    self.model_name = entry.provider.model_name
                    logger.info(
                        "llm_provider_result provider=%s model=%s operation=%s attempt=%d duration_ms=%d "
                        "result=success fallback_from=%s",
                        self.provider_name,
                        self.model_name,
                        operation,
                        attempt,
                        int((monotonic() - started) * 1000),
                        fallback_from,
                    )
                    return answer
            if last_error and last_error.category in _NO_FALLBACK:
                raise last_error
            fallback_from = config.name

        if last_error:
            raise last_error
        raise ProviderError("router", ProviderFailureCategory.UNKNOWN)


def _can_retry(category: ProviderFailureCategory, attempt: int, max_attempts: int) -> bool:
    if category in _NO_FALLBACK or category in {
        ProviderFailureCategory.AUTH_ERROR,
        ProviderFailureCategory.RATE_LIMIT,
        ProviderFailureCategory.QUOTA_EXHAUSTED,
    }:
        return False
    if category in {ProviderFailureCategory.TIMEOUT, ProviderFailureCategory.UNKNOWN}:
        return attempt < min(max_attempts, 2)
    return category in {
        ProviderFailureCategory.TRANSIENT_5XX,
        ProviderFailureCategory.NETWORK_ERROR,
    } and attempt < max_attempts


def _thai_request_is_eligible(question: str, records: list[ProcurementRecord]) -> bool:
    values = [question]
    for record in records:
        values.extend(
            [
                record.project_name,
                record.agency_name,
                record.winner_name,
                record.raw_text,
                record.normalized_text,
            ]
        )
    return not any(_PRIVATE_MARKERS.search(value or "") for value in values)
