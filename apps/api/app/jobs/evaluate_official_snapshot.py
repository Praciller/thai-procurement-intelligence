from __future__ import annotations

import json
import os
import time
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.data_sources.egp_contract import EGPContractSnapshot
from app.config import get_settings
from app.database import Base
from app.models import ProcurementRecord
from app.services.embeddings import generate_missing_embeddings, hash_embedding
from app.services.ingestion import import_rows, normalize_row
from app.services.llm.mock import MockLLMProvider
from app.services.provenance import read_json, validate_snapshot
from app.services.search import hybrid_candidates, keyword_candidates


ROOT = Path(__file__).parents[4]
SNAPSHOT = ROOT / "data/official/raw/dga-egp-contract-2568-250.csv"
METADATA = ROOT / "data/official/metadata/dga-egp-contract-2568-250.json"
REPORTS = ROOT / "reports/official_snapshot"
QUERIES = ("คอมพิวเตอร์", "น้ำมันเบรก", "วัสดุก่อสร้าง", "ซ่อมบำรุงรถยนต์")


def enriched_rows(metadata: dict) -> list[dict]:
    return [
        {
            **row,
            "source_url": metadata["source_url"],
            "source_snapshot_id": metadata["snapshot_id"],
            "source_retrieved_at": metadata["retrieved_at"],
            "source_updated_at": metadata.get("source_updated_at"),
            "source_license": metadata["license"],
            "source_checksum": metadata["sha256"],
            "mapping_version": metadata["mapping_version"],
        }
        for row in EGPContractSnapshot(SNAPSHOT).rows()
    ]


def quality(metadata: dict, rows: list[dict]) -> tuple[dict, dict, list[dict]]:
    valid = []
    rejected = []
    duplicates = 0
    seen = set()
    for number, row in enumerate(rows, start=1):
        try:
            normalized = normalize_row(row, dataset_type="official_snapshot")
            key = normalized["source_record_id"]
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            valid.append(normalized)
        except Exception as exc:
            rejected.append({"row_number": number, "source_record_id": row.get("source_record_id"), "error": str(exc)})

    fields = (
        "source_record_id",
        "project_name",
        "agency_name",
        "province",
        "procurement_method",
        "procurement_category",
        "budget_amount",
        "winning_amount",
        "announcement_date",
        "contract_date",
        "source_url",
    )
    completeness = {
        field: {
            "present": sum(record.get(field) is not None for record in valid),
            "total": len(valid),
            "rate": round(sum(record.get(field) is not None for record in valid) / len(valid), 4) if valid else 0,
        }
        for field in fields
    }
    dates = [record["announcement_date"] for record in valid if record.get("announcement_date")]
    warnings = sum(1 for record in valid if record.get("announcement_date") is None or record.get("province") is None)
    summary = {
        "snapshot_id": metadata["snapshot_id"],
        "checksum_verified": True,
        "raw_records": len(rows),
        "valid_records": len(valid),
        "rejected_records": len(rejected),
        "duplicate_records": duplicates,
        "warning_records": warnings,
        "ingestion_success_rate": round(len(valid) / len(rows), 4),
        "rejection_rate": round(len(rejected) / len(rows), 4),
        "duplicate_rate": round(duplicates / len(rows), 4),
        "coverage_start": min(dates).isoformat() if dates else None,
        "coverage_end": max(dates).isoformat() if dates else None,
        "mapping_version": metadata["mapping_version"],
        "limitations": ["First 250 unique projects from one source resource part; all rows in this subset use specific-selection procurement."],
    }
    return summary, completeness, rejected[:10]


def precision(results, query: str) -> float:
    if not results:
        return 0.0
    return sum(query.casefold() in result.record.project_name.casefold() for result in results) / len(results)


async def evaluation(metadata: dict, rows: list[dict]) -> dict:
    os.environ["DATASET_MODE"] = "official_snapshot"
    get_settings.cache_clear()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        _, first = import_rows(session, rows, EGPContractSnapshot.source_name, dataset_type="official_snapshot")
        _, second = import_rows(session, rows, EGPContractSnapshot.source_name, dataset_type="official_snapshot")
        generate_missing_embeddings(session)
        keyword_scores = []
        hybrid_scores = []
        latencies = []
        for query in QUERIES:
            started = time.perf_counter()
            keyword = keyword_candidates(session, query, limit=5)
            latencies.append((time.perf_counter() - started) * 1000)
            hybrid = hybrid_candidates(session, query, hash_embedding(query), limit=5)
            keyword_scores.append(precision(keyword, query))
            hybrid_scores.append(precision(hybrid, query))

        records = session.scalars(select(ProcurementRecord)).all()
        provider = MockLLMProvider()
        unsupported = 0
        for query in QUERIES:
            candidates = [item.record for item in keyword_candidates(session, query, limit=5)]
            answer = await provider.answer_question(query, candidates)
            if any(term in answer.casefold() for term in ("corrupt", "fraud", "ทุจริต")):
                unsupported += 1

        return {
            "snapshot_id": metadata["snapshot_id"],
            "query_count": len(QUERIES),
            "keyword_precision_at_5": round(sum(keyword_scores) / len(keyword_scores), 4),
            "hybrid_precision_at_5": round(sum(hybrid_scores) / len(hybrid_scores), 4),
            "citation_completeness": round(sum(bool(record.source_record_id) for record in records) / len(records), 4),
            "source_link_completeness": round(sum(bool(record.source_url) for record in records) / len(records), 4),
            "unsupported_claim_rate": round(unsupported / len(QUERIES), 4),
            "dataset_mode_isolation": all(record.dataset_type == "official_snapshot" for record in records),
            "idempotency": {
                "first_inserted": first.inserted_rows,
                "second_inserted": second.inserted_rows,
                "second_unchanged": second.unchanged_rows,
                "record_count_after_second_run": len(records),
            },
            "keyword_search_latency_ms": {
                "median": round(sorted(latencies)[len(latencies) // 2], 3),
                "max": round(max(latencies), 3),
                "environment": "in-memory SQLite, bounded local fixture",
            },
            "query_labels": list(QUERIES),
            "scope_note": "Bounded fixture evaluation; not production-scale or system-wide evidence.",
        }


def write_report(name: str, data: dict | list) -> None:
    (REPORTS / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def markdown(title: str, data: dict) -> str:
    rows = [f"# {title}", "", "Measured locally from the committed bounded official snapshot.", ""]
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue
        rows.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    rows.extend(["", "This snapshot is not representative of the entire Thai procurement system.", ""])
    return "\n".join(rows)


async def main() -> None:
    metadata = read_json(METADATA)
    validate_snapshot(SNAPSHOT, metadata)
    rows = enriched_rows(metadata)
    summary, completeness, rejected = quality(metadata, rows)
    metadata["coverage_start"] = summary["coverage_start"]
    metadata["coverage_end"] = summary["coverage_end"]
    METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORTS.mkdir(parents=True, exist_ok=True)
    write_report("data_quality_summary", summary)
    write_report("field_completeness", completeness)
    write_report("rejected_records_sample", rejected)
    (REPORTS / "data_quality_summary.md").write_text(markdown("Official Snapshot Data Quality", summary), encoding="utf-8")
    measured = await evaluation(metadata, rows)
    write_report("evaluation", measured)
    (REPORTS / "evaluation.md").write_text(markdown("Official Snapshot Evaluation", measured), encoding="utf-8")
    print(json.dumps({"quality": summary, "evaluation": measured}, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
