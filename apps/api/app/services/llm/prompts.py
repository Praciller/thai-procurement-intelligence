from pathlib import Path

from app.models import ProcurementRecord
from app.services.llm.base import format_record_context


_PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"
_SUMMARY_TEMPLATE = (_PROMPT_DIR / "summary.txt").read_text(encoding="utf-8")
_QA_TEMPLATE = (_PROMPT_DIR / "qa.txt").read_text(encoding="utf-8")


def summary_messages(record: ProcurementRecord) -> list[dict[str, str]]:
    system, user = _SUMMARY_TEMPLATE.split("\n\nUser:\n", maxsplit=1)
    user = user.format(
        structured_fields=format_record_context(record),
        raw_text=record.raw_text or record.normalized_text or "not available",
    )
    return [{"role": "system", "content": system.removeprefix("System:\n")}, {"role": "user", "content": user}]


def question_messages(question: str, records: list[ProcurementRecord]) -> list[dict[str, str]]:
    system, user = _QA_TEMPLATE.split("\n\nUser:\n", maxsplit=1)
    context = "\n\n".join(format_record_context(record) for record in records)
    user = user.format(question=question, context_records=context or "No records were retrieved.")
    return [{"role": "system", "content": system.removeprefix("System:\n")}, {"role": "user", "content": user}]
