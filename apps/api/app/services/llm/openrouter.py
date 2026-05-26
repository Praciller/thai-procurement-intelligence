import httpx

from app.config import Settings
from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider, format_record_context


class OpenRouterProvider(LLMProvider):
    provider_name = "openrouter"

    def __init__(self, settings: Settings):
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for OpenRouter provider")
        self.api_key = settings.openrouter_api_key
        self.model_name = settings.openrouter_model

    async def _chat(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "Use only supplied procurement evidence. Do not invent facts."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return await self._chat(f"Summarize this procurement record in Thai in 5 bullet points:\n\n{format_record_context(record)}")

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        context = "\n\n".join(format_record_context(record) for record in records)
        return await self._chat(f"Question:\n{question}\n\nRetrieved procurement records:\n{context}")

