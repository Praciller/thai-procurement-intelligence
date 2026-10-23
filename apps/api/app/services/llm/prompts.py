import hashlib
import json
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


def summary_cache_version(record: ProcurementRecord) -> str:
    """Cache by the actual rendered prompt and source identity, not a manual label.

    The column is VARCHAR(40): summary-v3- plus 29 SHA-256 hex characters.
    Both content edits and template wording changes invalidate old summaries.
    The provider/model are separate fields in the unique cache constraint.
    """
    encoded = json.dumps(
        {"content_hash": record.content_hash, "messages": summary_messages(record)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"summary-v3-{hashlib.sha256(encoded).hexdigest()[:29]}"
