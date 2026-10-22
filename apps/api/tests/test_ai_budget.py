from datetime import UTC, datetime

from sqlalchemy import func, select

from app.config import get_settings
from app.models import AIHourlyBudget, AIQALog
from app.services.ingestion import import_rows
from app.services.llm.budget import consume_hourly_budget
from app.services.llm.mock import MockLLMProvider


def test_shared_hourly_counter_enforces_limit_atomically(session):
    window = datetime(2026, 10, 22, 12, tzinfo=UTC)
    assert consume_hourly_budget(session, limit=2, now=window) is True
    assert consume_hourly_budget(session, limit=2, now=window) is True
    assert consume_hourly_budget(session, limit=2, now=window) is False
    assert session.scalar(select(AIHourlyBudget.requests)) == 2
    assert consume_hourly_budget(session, limit=2, now=window.replace(hour=13)) is True
    assert session.scalar(select(func.count()).select_from(AIHourlyBudget)) == 2
    assert consume_hourly_budget(session, limit=0, now=window) is False


def _seed(session):
    import_rows(
        session,
        [{"source_record_id": "C-1", "project_name": "Computer procurement",
          "agency_name": "Unit agency", "budget_amount": "100"}],
        "unit",
    )


class CountingExternal(MockLLMProvider):
    provider_name = "external-fixture"
    model_name = "fixed-test-model"

    def __init__(self):
        self.answer_calls = 0
        self.summary_calls = 0

    async def answer_question(self, question, records):
        self.answer_calls += 1
        return await super().answer_question(question, records)

    async def generate_summary(self, record):
        self.summary_calls += 1
        return await super().generate_summary(record)


def test_assistant_degrades_offline_at_quota_and_does_not_store_raw_qa_by_default(
    client, session, monkeypatch
):
    _seed(session)
    monkeypatch.setenv("ENABLE_LLM", "true")
    monkeypatch.setenv("AI_HOURLY_REQUEST_LIMIT", "1")
    monkeypatch.setenv("LOG_AI_QUERIES", "false")
    get_settings.cache_clear()
    provider = CountingExternal()
    monkeypatch.setattr("app.routers.assistant.get_llm_provider", lambda settings: provider)
    try:
        first = client.post("/api/assistant/ask", json={"question": "Computer"})
        second = client.post("/api/assistant/ask", json={"question": "Computer"})
        assert first.status_code == second.status_code == 200
        assert first.json()["ai_enabled"] is True
        assert second.json()["ai_enabled"] is False
        assert provider.answer_calls == 1
        assert session.scalar(select(AIHourlyBudget.requests)) == 1
        assert session.scalar(select(func.count()).select_from(AIQALog)) == 0
    finally:
        get_settings.cache_clear()


def test_summary_never_calls_external_when_hourly_budget_zero(client, session, monkeypatch):
    _seed(session)
    monkeypatch.setenv("ENABLE_LLM", "true")
    monkeypatch.setenv("AI_HOURLY_REQUEST_LIMIT", "0")
    get_settings.cache_clear()
    provider = CountingExternal()
    monkeypatch.setattr("app.routers.records.get_llm_provider", lambda settings: provider)
    record_id = client.get("/api/records").json()["items"][0]["id"]
    try:
        first = client.post(f"/api/records/{record_id}/summary")
        second = client.post(f"/api/records/{record_id}/summary")
        assert first.status_code == second.status_code == 200
        assert first.json()["provider"] == "mock"
        assert first.json()["cached"] is False
        assert second.json()["cached"] is True
        assert provider.summary_calls == 0
    finally:
        get_settings.cache_clear()


def test_qa_logging_is_only_enabled_by_explicit_opt_in(client, session, monkeypatch):
    _seed(session)
    monkeypatch.setenv("ENABLE_LLM", "false")
    monkeypatch.setenv("LOG_AI_QUERIES", "true")
    get_settings.cache_clear()
    try:
        response = client.post("/api/assistant/ask", json={"question": "Computer"})
        assert response.status_code == 200
        assert session.scalar(select(func.count()).select_from(AIQALog)) == 1
    finally:
        get_settings.cache_clear()
