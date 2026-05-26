from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    provider_name = "mock"
    model_name = "deterministic-local"

    async def generate_summary(self, record: ProcurementRecord) -> str:
        budget = f"{record.budget_amount:,.2f} THB" if record.budget_amount is not None else "not available"
        return "\n".join(
            [
                f"- Project purpose: {record.project_name}",
                f"- Agency: {record.agency_name or 'not available'}",
                f"- Budget or winning amount: {budget}",
                f"- Important dates: announcement {record.announcement_date or 'not available'}",
                f"- Method/category: {record.procurement_method or 'not available'} / {record.procurement_category or 'not available'}",
                "- Missing or uncertain information: mock summary uses stored public sample fields only.",
            ]
        )

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        if not records:
            return "Cannot determine from available procurement records."
        lines = ["Direct answer: retrieved records most relevant to the question are:"]
        for record in records[:5]:
            budget = f"{record.budget_amount:,.2f} THB" if record.budget_amount is not None else "budget not available"
            lines.append(f"- {record.project_name} ({record.agency_name or 'unknown agency'}, {budget})")
        lines.append("Evidence: answer is based only on cited retrieved records.")
        lines.append("Limitations: deterministic mock provider did not call an external LLM.")
        return "\n".join(lines)

