from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import IngestionError, IngestionRun, ProcurementRecord
from app.services.normalization import (
    clean_text,
    content_hash,
    normalize_agency,
    normalize_province,
    normalized_record_text,
    parse_date,
    parse_decimal,
)


FIELD_ALIASES = {
    "source_record_id": ["source_record_id", "project_id", "id", "source_id"],
    "project_name": ["project_name", "project", "name", "title"],
    "agency_name": ["agency_name", "agency", "department"],
    "province": ["province", "changwat"],
    "procurement_method": ["procurement_method", "method"],
    "procurement_category": ["procurement_category", "category", "procurement_type"],
    "budget_amount": ["budget_amount", "budget", "estimated_budget"],
    "winning_amount": ["winning_amount", "contract_amount", "winner_amount"],
    "winner_name": ["winner_name", "winner", "vendor"],
    "announcement_date": ["announcement_date", "announce_date", "published_at"],
    "contract_date": ["contract_date", "contract_signed_at"],
    "source_url": ["source_url", "url", "link"],
    "raw_text": ["raw_text", "description", "details"],
}


@dataclass
class ImportCounters:
    total_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    failed_rows: int = 0


def _lookup(row: dict[str, Any], field: str) -> Any:
    lower = {key.strip().casefold(): value for key, value in row.items()}
    for alias in FIELD_ALIASES[field]:
        if alias.casefold() in lower:
            return lower[alias.casefold()]
    return None


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "source_record_id": clean_text(_lookup(row, "source_record_id")),
        "project_name": clean_text(_lookup(row, "project_name")),
        "agency_name": normalize_agency(_lookup(row, "agency_name")),
        "province": normalize_province(_lookup(row, "province")),
        "procurement_method": clean_text(_lookup(row, "procurement_method")),
        "procurement_category": clean_text(_lookup(row, "procurement_category")),
        "budget_amount": parse_decimal(_lookup(row, "budget_amount")),
        "winning_amount": parse_decimal(_lookup(row, "winning_amount")),
        "winner_name": clean_text(_lookup(row, "winner_name")),
        "announcement_date": parse_date(_lookup(row, "announcement_date")),
        "contract_date": parse_date(_lookup(row, "contract_date")),
        "source_url": clean_text(_lookup(row, "source_url")),
        "raw_text": clean_text(_lookup(row, "raw_text")),
    }
    if not normalized["project_name"]:
        raise ValueError("project_name is required")
    normalized["content_hash"] = content_hash(normalized)
    normalized["normalized_text"] = normalized_record_text(normalized)
    return normalized


def _find_existing(session: Session, source_name: str, normalized: dict[str, Any]) -> ProcurementRecord | None:
    source_record_id = normalized.get("source_record_id")
    if source_record_id:
        existing = session.scalar(
            select(ProcurementRecord).where(
                ProcurementRecord.source_name == source_name,
                ProcurementRecord.source_record_id == source_record_id,
            )
        )
        if existing:
            return existing
    return session.scalar(select(ProcurementRecord).where(ProcurementRecord.content_hash == normalized["content_hash"]))


def import_rows(session: Session, rows: Iterable[dict[str, Any]], source_name: str) -> tuple[IngestionRun, ImportCounters]:
    run = IngestionRun(source_name=source_name, status="running")
    session.add(run)
    session.flush()
    counters = ImportCounters()

    for row_number, row in enumerate(rows, start=1):
        counters.total_rows += 1
        try:
            normalized = normalize_row(row)
            existing = _find_existing(session, source_name, normalized)
            if existing:
                for key, value in normalized.items():
                    setattr(existing, key, value)
                existing.source_name = source_name
                existing.imported_at = datetime.now(UTC)
                counters.updated_rows += 1
            else:
                session.add(ProcurementRecord(source_name=source_name, **normalized))
                counters.inserted_rows += 1
        except Exception as exc:  # keep row-level import resilient
            counters.failed_rows += 1
            session.add(
                IngestionError(
                    ingestion_run_id=run.id,
                    row_number=row_number,
                    raw_payload=dict(row),
                    error_message=str(exc),
                )
            )

    run.total_rows = counters.total_rows
    run.inserted_rows = counters.inserted_rows
    run.updated_rows = counters.updated_rows
    run.skipped_rows = counters.skipped_rows
    run.failed_rows = counters.failed_rows
    run.status = "completed_with_errors" if counters.failed_rows else "completed"
    run.finished_at = datetime.now(UTC)
    session.commit()
    session.refresh(run)
    return run, counters


def import_csv_file(session: Session, file_path: str | Path, source_name: str) -> tuple[IngestionRun, ImportCounters]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return import_rows(session, reader, source_name=source_name)

