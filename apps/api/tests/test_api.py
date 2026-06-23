import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProcurementRecord
from app.services.embeddings import generate_missing_embeddings
from app.services.ingestion import import_rows


def seed(session: Session):
    rows = [
        {
            "source_record_id": "IT-1",
            "project_name": "IT cybersecurity monitoring subscription",
            "agency_name": "Sample Digital Service Center F",
            "province": "Bangkok",
            "procurement_method": "e-bidding",
            "procurement_category": "IT",
            "budget_amount": "2200000",
            "announcement_date": "2025-03-10",
            "raw_text": "Sample cybersecurity monitoring procurement for public service.",
        },
        {
            "source_record_id": "CON-1",
            "project_name": "ก่อสร้างระบบระบายน้ำชุมชนตัวอย่าง",
            "agency_name": "Sample Municipality B",
            "province": "Chiang Mai",
            "procurement_method": "specific selection",
            "procurement_category": "Construction",
            "budget_amount": "1800000",
            "announcement_date": "2025-04-12",
            "raw_text": "Sample drainage construction procurement.",
        },
    ]
    import_rows(session, rows, "unit")
    generate_missing_embeddings(session)


def test_records_search_filters(client: TestClient, session: Session):
    seed(session)

    response = client.get("/api/records?province=Bangkok&q=cybersecurity")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["procurement_category"] == "IT"


def test_readiness_reports_database_and_record_count(client: TestClient, session: Session):
    seed(session)

    response = client.get("/api/health/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "ready",
        "database": "ok",
        "record_count": 2,
        "dataset_mode": "synthetic",
    }


def test_dashboard_aggregation(client: TestClient, session: Session):
    seed(session)

    response = client.get("/api/analytics/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 2
    assert data["total_budget"] == "4000000.00"
    assert data["records_by_province"][0]["count"] == 1


def test_summary_is_cached(client: TestClient, session: Session):
    seed(session)
    record = client.get("/api/records?q=cybersecurity").json()["items"][0]

    first = client.post(f"/api/records/{record['id']}/summary")
    second = client.post(f"/api/records/{record['id']}/summary")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert "Project purpose" in second.json()["summary_text"]


@pytest.mark.parametrize("action", ["summary", "embedding"])
def test_record_mutations_reject_inactive_dataset(client: TestClient, session: Session, action: str):
    import_rows(
        session,
        [
            {
                "source_record_id": "OFFICIAL-1",
                "project_name": "Official inactive record",
                "agency_name": "Official agency",
                "source_url": "https://data.go.th/dataset/example",
                "source_snapshot_id": "fixture",
                "source_license": "Creative Commons Attributions",
                "source_checksum": "a" * 64,
                "mapping_version": "dga-egp-v1",
            }
        ],
        "dga_egp",
        dataset_type="official_snapshot",
    )
    record = session.scalar(select(ProcurementRecord))

    response = client.post(f"/api/records/{record.id}/{action}")

    assert response.status_code == 404


def test_assistant_returns_evidence_when_llm_disabled(client: TestClient, session: Session):
    seed(session)

    response = client.post("/api/assistant/ask", json={"question": "highest budget IT project", "limit": 4})

    assert response.status_code == 200
    data = response.json()
    assert data["ai_enabled"] is False
    assert data["citations"]
    assert data["retrieved_records"]


def test_assistant_refuses_when_no_evidence_exists(client: TestClient):
    response = client.post("/api/assistant/ask", json={"question": "unsupported allegation", "limit": 4})

    assert response.status_code == 200
    assert response.json()["answer"] == "Cannot determine from available procurement records."
    assert response.json()["citations"] == []
