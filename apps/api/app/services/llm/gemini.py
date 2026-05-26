import httpx

from app.config import Settings
from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider, format_record_context


class GeminiProvider(LLMProvider):
    provider_name = "gemini"
    model_name = "gemini-1.5-flash"

    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini provider")
        self.api_key = settings.gemini_api_key

    async def _generate(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_summary(self, record: ProcurementRecord) -> str:
        prompt = (
            "You summarize Thai public procurement records. Use only provided fields. "
            "If missing, say not available.\n\nSummarize in Thai in 5 bullet points.\n\n"
            f"{format_record_context(record)}"
        )
        return await self._generate(prompt)

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        context = "\n\n".join(format_record_context(record) for record in records)
        prompt = (
            "Answer using only the provided procurement records. Cite record IDs or project names. "
            "If unsupported, say you cannot determine from available data.\n\n"
            f"Question:\n{question}\n\nRetrieved procurement records:\n{context}"
        )
        return await self._generate(prompt)

