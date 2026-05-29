from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.fetch_source import import_source_url
from app.models import IngestionError, ProcurementRecord
from app.services.ingestion import import_rows


def test_csv_import_valid_rows(session: Session):
    rows = [
        {
            "source_record_id": "A-1",
            "project_name": "IT network upgrade",
            "agency_name": " Sample Municipality B ",
            "province": "bkk",
            "procurement_method": "e-bidding",
            "procurement_category": "IT",
            "budget_amount": "1,250,000",
            "announcement_date": "2025-01-15",
        },
        {
            "source_record_id": "A-2",
            "project_name": "Construction drainage work",
            "agency_name": "Sample Provincial Office A",
            "province": "Chiang Mai",
            "budget_amount": "500000",
            "announcement_date": "15/02/2568",
        },
    ]

    run, counters = import_rows(session, rows, "unit")

    records = session.scalars(select(ProcurementRecord)).all()
    assert run.status == "completed"
    assert counters.inserted_rows == 2
    assert records[0].province == "Bangkok"
    assert str(records[0].budget_amount) == "1250000.00"
    assert records[1].announcement_date.isoformat() == "2025-02-15"


def test_csv_import_logs_invalid_rows(session: Session):
    run, counters = import_rows(session, [{"source_record_id": "bad", "budget_amount": "oops"}], "unit")

    error = session.scalar(select(IngestionError))
    assert run.status == "completed_with_errors"
    assert counters.failed_rows == 1
    assert error is not None
    assert "project_name is required" in error.error_message


def test_csv_import_deduplicates_by_source_record_id(session: Session):
    row = {
        "source_record_id": "A-1",
        "project_name": "IT network upgrade",
        "agency_name": "Sample Municipality B",
        "province": "Bangkok",
        "budget_amount": "1000",
        "announcement_date": "2025-01-15",
    }

    import_rows(session, [row], "unit")
    import_rows(session, [{**row, "budget_amount": "2000"}], "unit")

    records = session.scalars(select(ProcurementRecord)).all()
    assert len(records) == 1
    assert str(records[0].budget_amount) == "2000.00"


def test_fetch_source_imports_open_api_rows(monkeypatch, session: Session):
    class FakeOpenApiDataSource:
        def __init__(self, url: str, source_name: str):
            self.url = url
            self.source_name = source_name

        def rows(self):
            return iter(
                [
                    {
                        "source_record_id": "LIVE-1",
                        "project_name": "Public API bridge repair procurement",
                        "agency_name": "Sample Roads Department",
                        "province": "Chonburi",
                        "budget_amount": "3000000",
                        "announcement_date": "2025-05-01",
                    }
                ]
            )

    monkeypatch.setattr("app.jobs.fetch_source.OpenApiDataSource", FakeOpenApiDataSource)

    run, counters = import_source_url(session, "https://example.test/procurement.json", "public_api")

    record = session.scalar(select(ProcurementRecord))
    assert run.source_name == "public_api"
    assert counters.inserted_rows == 1
    assert record is not None
    assert record.source_record_id == "LIVE-1"
