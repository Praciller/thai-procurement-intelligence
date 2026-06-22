from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import ProcurementRecord

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness(session: Session = Depends(get_session)) -> dict[str, int | str]:
    mode = get_settings().dataset_mode
    try:
        record_count = session.scalar(select(func.count(ProcurementRecord.id)).where(ProcurementRecord.dataset_type == mode))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    return {
        "status": "ready",
        "database": "ok",
        "record_count": int(record_count or 0),
        "dataset_mode": mode,
    }
