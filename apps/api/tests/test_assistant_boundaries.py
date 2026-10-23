"""Public API validation and external inference budget safeguards."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIHourlyBudget, ProcurementRecord
from app.services.ingestion import import_rows
from app.services.llm.mock import MockLLMProvider


def _seed(session: Session) -> ProcurementRecord:
    import_rows(
        session,
        [{
            "source_record_id": "FILTER-1",
            "project_name": "Computer cybersecurity maintenance",
            "agency_name": "Test municipality",
            "province": "Bangkok",
            "procurement_category": "IT",
            "budget_amount": "5000",
            "announcement_date": "2025-03-10",
            "raw_text": "Computer services and network maintenance",
        }],
        "validation_fixture",
    )
    record = session.scalar(
        select(ProcurementRecord).where(ProcurementRecord.source_record_id == "FILTER-1")
    )
    assert record is not None
    return record


@pytest.mark.parametrize(
    "filters",
    [
        {"min_budget": {"unexpected": 1}},
        {"min_budget": "Infinity"},
        {"min_budget": -1},
        {"min_budget": 9000, "max_budget": 200},
        {"date_from": "yesterday"},
        {"date_from": "2025-04-01", "date_to": "2025-03-01"},
        {"unrecognized": "anything"},
        {"q": "ignored filter"},
        {"province": ["Bangkok"]},
        {"agency": {"operator": "contains"}},
    ],
)
def test_assistant_rejects_invalid_filter_payloads(client: TestClient, filters: dict):
    response = client.post("/api/assistant/ask", json={"question": "Computer", "filters": filters})
    assert response.status_code == 422


def test_assistant_supports_valid_typed_filters(client: TestClient, session: Session):
    _seed(session)
    response = client.post(
        "/api/assistant/ask",
        json={
            "question": "Computer",
            "filters": {
                "province": "Bangkok",
                "category": "IT",
                "min_budget": 5000,
                "max_budget": 5000,
                "date_from": "2025-03-01",
                "date_to": "2025-03-31",
            },
        },
    )
    assert response.status_code == 200
    assert len(response.json()["citations"]) == 1

    excluded = client.post(
        "/api/assistant/ask",
        json={"question": "Computer", "filters": {"min_budget": 6000}},
    )
    assert excluded.status_code == 200
    assert excluded.json()["citations"] == []


class ExternalFixture(MockLLMProvider):
    provider_name = "external-fixture"
    model_name = "external-fixture-model"

    def __init__(self):
        self.calls = 0

    async def answer_question(self, question, records):
        self.calls += 1
        return await super().answer_question(question, records)

    async def generate_summary(self, record):
        self.calls += 1
        return await super().generate_summary(record)


@pytest.mark.parametrize("endpoint", ["assistant", "summary"])
def test_oversized_record_context_never_reaches_external_provider_or_consumes_budget(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
):
    record = _seed(session)
    record.raw_text = "X" * 25_000
    session.commit()

    monkeypatch.setenv("ENABLE_LLM", "true")
    monkeypatch.setenv("AI_HOURLY_REQUEST_LIMIT", "10")
    get_settings.cache_clear()
    external = ExternalFixture()
    handler = "app.routers.assistant" if endpoint == "assistant" else "app.routers.records"
    monkeypatch.setattr(f"{handler}.get_llm_provider", lambda settings: external)

    try:
        if endpoint == "assistant":
            response = client.post("/api/assistant/ask", json={"question": "Computer"})
        else:
            response = client.post(f"/api/records/{record.id}/summary")
        assert response.status_code == 413
        assert external.calls == 0
        assert session.scalar(select(func.count()).select_from(AIHourlyBudget)) == 0
    finally:
        get_settings.cache_clear()


def test_large_local_mock_context_remains_available(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    record = _seed(session)
    record.raw_text = "X" * 25_000
    session.commit()
    monkeypatch.setenv("ENABLE_LLM", "false")
    get_settings.cache_clear()
    try:
        response = client.post(f"/api/records/{record.id}/summary")
        assert response.status_code == 200
        assert response.json()["provider"] == "mock"
    finally:
        get_settings.cache_clear()
