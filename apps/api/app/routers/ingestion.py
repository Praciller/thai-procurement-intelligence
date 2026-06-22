from tempfile import NamedTemporaryFile
from pathlib import Path
from secrets import compare_digest

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import IngestionRun
from app.schemas import ImportResult, IngestionRunResponse
from app.services.ingestion import import_csv_file

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/import-csv", response_model=ImportResult)
async def import_csv(
    source_name: str = "manual_upload",
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    x_admin_token: str | None = Header(None),
):
    expected = get_settings().admin_ingestion_token
    if not expected or not x_admin_token or not compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="ingestion is disabled")
    if file.content_type not in {"text/csv", "application/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=415, detail="CSV upload required")
    payload = await file.read(2_000_001)
    if len(payload) > 2_000_000:
        raise HTTPException(status_code=413, detail="upload exceeds 2 MB")
    with NamedTemporaryFile("wb", suffix=".csv", delete=False) as temp_file:
        temp_file.write(payload)
        temp_path = temp_file.name
    try:
        run, counters = import_csv_file(session, temp_path, source_name=source_name)
    finally:
        Path(temp_path).unlink(missing_ok=True)
    return ImportResult(run_id=run.id, status=run.status, **counters.__dict__)


@router.get("/status", response_model=list[IngestionRunResponse])
def ingestion_status(session: Session = Depends(get_session)) -> list[IngestionRunResponse]:
    settings = get_settings()
    mode_filter = IngestionRun.snapshot_id.is_not(None) if settings.dataset_mode == "official_snapshot" else IngestionRun.snapshot_id.is_(None)
    runs = session.scalars(select(IngestionRun).where(mode_filter).order_by(IngestionRun.started_at.desc()).limit(10)).all()
    return [IngestionRunResponse.model_validate(run) for run in runs]
