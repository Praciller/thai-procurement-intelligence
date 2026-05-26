from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas import AnalyticsOverview
from app.services.analytics import analytics_overview

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(session: Session = Depends(get_session)) -> AnalyticsOverview:
    return analytics_overview(session)

