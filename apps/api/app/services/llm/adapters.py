from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import httpx

from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider
from app.services.llm.errors import ProviderError, ProviderFailureCategory
from app.services.llm.provider_config import ProviderConfig
from app.services.llm.prompts import question_messages, summary_messages


def _category_for_status(status_code: int) -> ProviderFailureCategory:
    if status_code in (401, 403):
        return ProviderFailureCategory.AUTH_ERROR
    if status_code in (400, 422):
        return ProviderFailureCategory.BAD_REQUEST
    if status_code == 402:
        return ProviderFailureCategory.QUOTA_EXHAUSTED
    if status_code in (408, 409, 425, 429):
        return ProviderFailureCategory.RATE_LIMIT
    if status_code >= 500:
        return ProviderFailureCategory.TRANSIENT_5XX
    return ProviderFailureCategory.UNKNOWN


def _text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(str(item.get("text", "")) for item in value if isinstance(item, dict)).strip()
    return ""


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        self.config = config
        self.provider_name = config.name
        self.model_name = config.model
        self._api_key = api_key

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return await self._complete(summary_messages(record))

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        return await self._complete(question_messages(question, records))

    async def _complete(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
        }
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.TIMEOUT, model_name=self.model_name) from exc
        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.NETWORK_ERROR, model_name=self.model_name) from exc

        if response.status_code >= 400:
            raise ProviderError(
                self.provider_name,
                _category_for_status(response.status_code),
                model_name=self.model_name,
                status_code=response.status_code,
            )
        try:
            data = response.json()
            message = data["choices"][0]["message"]
            content = _text_content(message.get("content"))
            actual_model = data.get("model")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.UNKNOWN, model_name=self.model_name) from exc
        if not content:
            raise ProviderError(self.provider_name, ProviderFailureCategory.UNKNOWN, model_name=self.model_name)
        if isinstance(actual_model, str) and actual_model:
            self.model_name = actual_model
        return content


class GeminiNativeProvider(LLMProvider):
    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        self.config = config
        self.provider_name = config.name
        self.model_name = config.model
        self._api_key = api_key

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return await self._complete(summary_messages(record))

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        return await self._complete(question_messages(question, records))

    async def _complete(self, messages: list[dict[str, str]]) -> str:
        system_messages = [message["content"] for message in messages if message["role"] == "system"]
        user_messages = [message["content"] for message in messages if message["role"] == "user"]
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": "\n\n".join(user_messages)}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        }
        if system_messages:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_messages)}]}
        url = f"{self.config.base_url.rstrip('/')}/models/{self.config.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    url,
                    headers={"x-goog-api-key": self._api_key},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.TIMEOUT, model_name=self.model_name) from exc
        except httpx.RequestError as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.NETWORK_ERROR, model_name=self.model_name) from exc

        if response.status_code >= 400:
            raise ProviderError(
                self.provider_name,
                _category_for_status(response.status_code),
                model_name=self.model_name,
                status_code=response.status_code,
            )
        try:
            data = response.json()
            parts: Iterable[dict[str, Any]] = data["candidates"][0]["content"]["parts"]
            content = "".join(str(part.get("text", "")) for part in parts).strip()
            actual_model = data.get("modelVersion")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(self.provider_name, ProviderFailureCategory.UNKNOWN, model_name=self.model_name) from exc
        if not content:
            raise ProviderError(self.provider_name, ProviderFailureCategory.UNKNOWN, model_name=self.model_name)
        if isinstance(actual_model, str) and actual_model:
            self.model_name = actual_model
        return content
