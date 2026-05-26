from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models import ProcurementRecord
from app.schemas import AnalyticsBucket, AnalyticsOverview, ProcurementRecordListItem


def _budget(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


def analytics_overview(session: Session) -> AnalyticsOverview:
    total_records = session.scalar(select(func.count(ProcurementRecord.id))) or 0
    total_budget = _budget(session.scalar(select(func.coalesce(func.sum(ProcurementRecord.budget_amount), 0))))
    average_budget = _budget(session.scalar(select(func.coalesce(func.avg(ProcurementRecord.budget_amount), 0))))

    def buckets(field, limit: int = 10) -> list[AnalyticsBucket]:
        rows = session.execute(
            select(field, func.count(ProcurementRecord.id), func.coalesce(func.sum(ProcurementRecord.budget_amount), 0))
            .group_by(field)
            .order_by(func.count(ProcurementRecord.id).desc())
            .limit(limit)
        ).all()
        return [AnalyticsBucket(label=str(label or "Unknown"), count=count, total_budget=budget) for label, count, budget in rows]

    month_expr = extract("month", ProcurementRecord.announcement_date)
    year_expr = extract("year", ProcurementRecord.announcement_date)
    month_rows = session.execute(
        select(year_expr, month_expr, func.count(ProcurementRecord.id), func.coalesce(func.sum(ProcurementRecord.budget_amount), 0))
        .where(ProcurementRecord.announcement_date.is_not(None))
        .group_by(year_expr, month_expr)
        .order_by(year_expr, month_expr)
    ).all()
    records_by_month = [
        AnalyticsBucket(label=f"{int(year):04d}-{int(month):02d}", count=count, total_budget=budget)
        for year, month, count, budget in month_rows
    ]

    top_projects = session.scalars(
        select(ProcurementRecord).order_by(ProcurementRecord.budget_amount.desc().nullslast()).limit(8)
    ).all()

    return AnalyticsOverview(
        total_records=total_records,
        total_budget=total_budget,
        average_budget=average_budget,
        records_by_province=buckets(ProcurementRecord.province),
        records_by_category=buckets(ProcurementRecord.procurement_category),
        records_by_month=records_by_month,
        top_agencies=buckets(ProcurementRecord.agency_name),
        top_projects=[ProcurementRecordListItem.model_validate(record) for record in top_projects],
    )

