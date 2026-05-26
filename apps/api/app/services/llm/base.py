from abc import ABC, abstractmethod

from app.models import ProcurementRecord


class LLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    async def generate_summary(self, record: ProcurementRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        raise NotImplementedError


def format_record_context(record: ProcurementRecord) -> str:
    return "\n".join(
        [
            f"ID: {record.id}",
            f"Project: {record.project_name}",
            f"Agency: {record.agency_name or 'not available'}",
            f"Province: {record.province or 'not available'}",
            f"Category: {record.procurement_category or 'not available'}",
            f"Method: {record.procurement_method or 'not available'}",
            f"Budget: {record.budget_amount or 'not available'}",
            f"Date: {record.announcement_date or 'not available'}",
            f"Text: {record.raw_text or record.normalized_text or 'not available'}",
        ]
    )

