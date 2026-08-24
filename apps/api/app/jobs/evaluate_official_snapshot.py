from __future__ import annotations

import json
import math
import os
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
JUDGMENTS = ROOT / "evals/retrieval/official_snapshot_judgments.json"


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


def score_ranking(ranked_source_ids: list[str], relevant_source_ids: set[str], k: int = 5) -> dict:
    top_k = ranked_source_ids[:k]
    false_positive_count = sum(source_id not in relevant_source_ids for source_id in top_k)
    if not relevant_source_ids:
        return {
            "precision_at_k": None,
            "recall_at_k": None,
            "ndcg_at_k": None,
            "mrr": None,
            "false_positive_count": false_positive_count,
            "eligible_for_relevance_average": False,
        }

    relevance = [1 if source_id in relevant_source_ids else 0 for source_id in top_k]
    hits = sum(relevance)
    dcg = sum(rel / math.log2(rank + 1) for rank, rel in enumerate(relevance, start=1))
    ideal_hits = min(len(relevant_source_ids), k)
    ideal_dcg = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    first_relevant_rank = next((rank for rank, rel in enumerate(relevance, start=1) if rel), None)
    return {
        "precision_at_k": hits / k,
        "recall_at_k": hits / len(relevant_source_ids),
        "ndcg_at_k": dcg / ideal_dcg if ideal_dcg else 0.0,
        "mrr": 1 / first_relevant_rank if first_relevant_rank else 0.0,
        "false_positive_count": false_positive_count,
        "eligible_for_relevance_average": True,
    }


def validate_judgments(judgments: dict, known_source_ids: set[str]) -> None:
    for query in judgments.get("queries", []):
        relevant_ids = set(query.get("relevant_source_record_ids", []))
        unknown = sorted(relevant_ids - known_source_ids)
        if unknown:
            raise ValueError(f"Judgment references unknown snapshot IDs: {', '.join(unknown)}")


def summarize_judged_metrics(metrics: list[dict], k: int = 5) -> dict:
    positive = [metric for metric in metrics if metric["eligible_for_relevance_average"]]
    negative = [metric for metric in metrics if not metric["eligible_for_relevance_average"]]

    def mean(key: str) -> float:
        return sum(float(metric[key]) for metric in positive) / len(positive) if positive else 0.0

    return {
        "positive_query_count": len(positive),
        "negative_query_count": len(negative),
        f"mean_precision_at_{k}": mean("precision_at_k"),
        f"mean_recall_at_{k}": mean("recall_at_k"),
        f"mean_ndcg_at_{k}": mean("ndcg_at_k"),
        "mean_mrr": mean("mrr"),
        "negative_false_positive_count": sum(int(metric["false_positive_count"]) for metric in negative),
    }


async def evaluation(metadata: dict, rows: list[dict]) -> dict:
    os.environ["DATASET_MODE"] = "official_snapshot"
    get_settings.cache_clear()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        _, first = import_rows(session, rows, EGPContractSnapshot.source_name, dataset_type="official_snapshot")
        _, second = import_rows(session, rows, EGPContractSnapshot.source_name, dataset_type="official_snapshot")
        generate_missing_embeddings(session)
        records = session.scalars(select(ProcurementRecord)).all()
        known_source_ids = {record.source_record_id for record in records if record.source_record_id}
        judgments = read_json(JUDGMENTS)
        if judgments.get("snapshot_id") != metadata["snapshot_id"]:
            raise ValueError("Retrieval judgments target a different snapshot")
        validate_judgments(judgments, known_source_ids)

        k = int(judgments.get("k", 5))
        keyword_metrics: list[dict] = []
        hybrid_metrics: list[dict] = []
        per_query: list[dict] = []
        for query_spec in judgments["queries"]:
            query = query_spec["query"]
            relevant_ids = set(query_spec["relevant_source_record_ids"])
            keyword = keyword_candidates(session, query, limit=k)
            hybrid = hybrid_candidates(session, query, hash_embedding(query), limit=k)
            keyword_ranked = [item.record.source_record_id for item in keyword if item.record.source_record_id]
            hybrid_ranked = [item.record.source_record_id for item in hybrid if item.record.source_record_id]
            keyword_score = score_ranking(keyword_ranked, relevant_ids, k=k)
            hybrid_score = score_ranking(hybrid_ranked, relevant_ids, k=k)
            keyword_metrics.append(keyword_score)
            hybrid_metrics.append(hybrid_score)
            per_query.append(
                {
                    "id": query_spec["id"],
                    "query": query,
                    "relevance_rule": query_spec["relevance_rule"],
                    "relevant_count": len(relevant_ids),
                    "keyword_ranked_source_record_ids": keyword_ranked,
                    "hybrid_ranked_source_record_ids": hybrid_ranked,
                    "keyword": keyword_score,
                    "hybrid": hybrid_score,
                }
            )

        keyword_summary = summarize_judged_metrics(keyword_metrics, k=k)
        hybrid_summary = summarize_judged_metrics(hybrid_metrics, k=k)
        provider = MockLLMProvider()
        forbidden_claim_hits = 0
        positive_queries = [query for query in judgments["queries"] if query["relevant_source_record_ids"]]
        for query_spec in positive_queries:
            candidates = [item.record for item in keyword_candidates(session, query_spec["query"], limit=k)]
            answer = await provider.answer_question(query_spec["query"], candidates)
            if any(term in answer.casefold() for term in ("corrupt", "fraud", "\u0e17\u0e38\u0e08\u0e23\u0e34\u0e15")):
                forbidden_claim_hits += 1

        return {
            "snapshot_id": metadata["snapshot_id"],
            "judgment_set": str(JUDGMENTS.relative_to(ROOT)).replace("\\", "/"),
            "judged_query_count": len(judgments["queries"]),
            "positive_query_count": keyword_summary["positive_query_count"],
            "negative_query_count": keyword_summary["negative_query_count"],
            f"keyword_mean_precision_at_{k}": round(keyword_summary[f"mean_precision_at_{k}"], 4),
            f"keyword_mean_recall_at_{k}": round(keyword_summary[f"mean_recall_at_{k}"], 4),
            f"keyword_mean_ndcg_at_{k}": round(keyword_summary[f"mean_ndcg_at_{k}"], 4),
            "keyword_mean_mrr": round(keyword_summary["mean_mrr"], 4),
            "keyword_negative_false_positive_count": keyword_summary["negative_false_positive_count"],
            f"hybrid_mean_precision_at_{k}": round(hybrid_summary[f"mean_precision_at_{k}"], 4),
            f"hybrid_mean_recall_at_{k}": round(hybrid_summary[f"mean_recall_at_{k}"], 4),
            f"hybrid_mean_ndcg_at_{k}": round(hybrid_summary[f"mean_ndcg_at_{k}"], 4),
            "hybrid_mean_mrr": round(hybrid_summary["mean_mrr"], 4),
            "hybrid_negative_false_positive_count": hybrid_summary["negative_false_positive_count"],
            "citation_completeness": round(sum(bool(record.source_record_id) for record in records) / len(records), 4),
            "source_link_completeness": round(sum(bool(record.source_url) for record in records) / len(records), 4),
            "forbidden_claim_term_rate": round(forbidden_claim_hits / len(positive_queries), 4),
            "dataset_mode_isolation": all(record.dataset_type == "official_snapshot" for record in records),
            "idempotency": {
                "first_inserted": first.inserted_rows,
                "second_inserted": second.inserted_rows,
                "second_unchanged": second.unchanged_rows,
                "record_count_after_second_run": len(records),
            },
            "label_policy": judgments["label_policy"],
            "per_query": per_query,
            "scope_note": "Bounded judged retrieval benchmark on one 250-record snapshot; deterministic hash vectors are a review aid, not production semantic embeddings.",
        }



def console_json(data: dict | list) -> str:
    return json.dumps(data, ensure_ascii=True)


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
    print(console_json({"quality": summary, "evaluation": measured}))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
