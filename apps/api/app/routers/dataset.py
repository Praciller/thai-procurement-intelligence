from pathlib import Path
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import IngestionRun, ProcurementRecord
from app.schemas import DatasetStatus, IngestionRunResponse
from app.services.provenance import freshness_status, read_json

router = APIRouter(prefix="/dataset", tags=["dataset"])


def _read_if_present(path: str) -> dict | None:
    target = Path(path)
    candidates = [target] if target.is_absolute() else [target, *(parent / target for parent in Path(__file__).resolve().parents)]
    match = next((candidate for candidate in candidates if candidate.is_file()), None)
    return read_json(match) if match else None


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=value.tzinfo or UTC).isoformat()


def _official_record_evidence(session: Session) -> tuple[dict | None, dict | None]:
    official = ProcurementRecord.dataset_type == "official_snapshot"
    record = session.scalar(
        select(ProcurementRecord)
        .where(official, ProcurementRecord.source_snapshot_id.is_not(None))
        .order_by(ProcurementRecord.imported_at.desc())
        .limit(1)
    )
    if record is None:
        return None, None

    count, checksum_count, distinct_checksums, coverage_start, coverage_end = session.execute(
        select(
            func.count(ProcurementRecord.id),
            func.count(ProcurementRecord.source_checksum),
            func.count(func.distinct(ProcurementRecord.source_checksum)),
            func.min(ProcurementRecord.announcement_date),
            func.max(ProcurementRecord.announcement_date),
        ).where(official)
    ).one()
    source = {
        "snapshot_id": record.source_snapshot_id,
        "source_name": record.source_name,
        "source_url": record.source_url,
        "retrieved_at": _iso_utc(record.source_retrieved_at),
        "coverage_start": coverage_start.isoformat() if coverage_start else None,
        "coverage_end": coverage_end.isoformat() if coverage_end else None,
        "license": record.source_license,
        "sha256": record.source_checksum,
        "record_count_raw": count,
        "mapping_version": record.mapping_version,
    }
    quality = {
        "checksum_verified": count > 0 and checksum_count == count and distinct_checksums == 1,
        "valid_records": count,
        "rejected_records": 0,
        "duplicate_records": 0,
    }
    return source, quality


@router.get("/status", response_model=DatasetStatus)
def dataset_status(session: Session = Depends(get_session)) -> DatasetStatus:
    settings = get_settings()
    mode_filter = IngestionRun.snapshot_id.is_not(None) if settings.dataset_mode == "official_snapshot" else IngestionRun.snapshot_id.is_(None)
    latest = session.scalar(select(IngestionRun).where(mode_filter).order_by(IngestionRun.started_at.desc(), IngestionRun.finished_at.desc()).limit(1))
    source = _read_if_present(settings.official_snapshot_metadata) if settings.dataset_mode == "official_snapshot" else None
    quality = _read_if_present(settings.official_quality_report) if settings.dataset_mode == "official_snapshot" else None
    if settings.dataset_mode == "official_snapshot" and (source is None or quality is None):
        fallback_source, fallback_quality = _official_record_evidence(session)
        source = source or fallback_source
        quality = quality or fallback_quality
    return DatasetStatus(
        dataset_mode=settings.dataset_mode,
        freshness_status=freshness_status(source.get("retrieved_at")) if source else "not_applicable",
        source=source,
        quality=quality,
        latest_run=IngestionRunResponse.model_validate(latest) if latest else None,
    )
