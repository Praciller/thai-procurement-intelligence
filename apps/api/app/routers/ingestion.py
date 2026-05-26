from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import IngestionRun
from app.schemas import ImportResult, IngestionRunResponse
from app.services.ingestion import import_csv_file

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/import-csv", response_model=ImportResult)
async def import_csv(source_name: str = "manual_upload", file: UploadFile = File(...), session: Session = Depends(get_session)):
    with NamedTemporaryFile("wb", suffix=".csv", delete=False) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name
    run, counters = import_csv_file(session, temp_path, source_name=source_name)
    return ImportResult(run_id=run.id, status=run.status, **counters.__dict__)


@router.get("/status", response_model=list[IngestionRunResponse])
def ingestion_status(session: Session = Depends(get_session)) -> list[IngestionRunResponse]:
    runs = session.scalars(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(10)).all()
    return [IngestionRunResponse.model_validate(run) for run in runs]

