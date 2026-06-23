from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import IngestionRun
from app.schemas import DatasetStatus, IngestionRunResponse
from app.services.provenance import freshness_status, read_json

router = APIRouter(prefix="/dataset", tags=["dataset"])


def _read_if_present(path: str) -> dict | None:
    target = Path(path)
    candidates = [target] if target.is_absolute() else [target, *(parent / target for parent in Path(__file__).resolve().parents)]
    match = next((candidate for candidate in candidates if candidate.is_file()), None)
    return read_json(match) if match else None


@router.get("/status", response_model=DatasetStatus)
def dataset_status(session: Session = Depends(get_session)) -> DatasetStatus:
    settings = get_settings()
    mode_filter = IngestionRun.snapshot_id.is_not(None) if settings.dataset_mode == "official_snapshot" else IngestionRun.snapshot_id.is_(None)
    latest = session.scalar(select(IngestionRun).where(mode_filter).order_by(IngestionRun.started_at.desc()).limit(1))
    source = _read_if_present(settings.official_snapshot_metadata) if settings.dataset_mode == "official_snapshot" else None
    quality = _read_if_present(settings.official_quality_report) if settings.dataset_mode == "official_snapshot" else None
    return DatasetStatus(
        dataset_mode=settings.dataset_mode,
        freshness_status=freshness_status(source.get("retrieved_at")) if source else "not_applicable",
        source=source,
        quality=quality,
        latest_run=IngestionRunResponse.model_validate(latest) if latest else None,
    )
