import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import ProcurementRecord

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/records.csv")
def export_records(session: Session = Depends(get_session)) -> Response:
    rows = session.scalars(select(ProcurementRecord).order_by(ProcurementRecord.announcement_date.desc())).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "project_name",
            "agency_name",
            "province",
            "procurement_method",
            "procurement_category",
            "budget_amount",
            "announcement_date",
            "source_url",
        ]
    )
    for record in rows:
        writer.writerow(
            [
                record.id,
                record.project_name,
                record.agency_name,
                record.province,
                record.procurement_method,
                record.procurement_category,
                record.budget_amount,
                record.announcement_date,
                record.source_url,
            ]
        )
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="procurement_records.csv"'},
    )

