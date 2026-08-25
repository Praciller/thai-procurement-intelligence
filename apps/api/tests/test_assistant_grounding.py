from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ProcurementRecord
from app.services.llm.base import LLMProvider
from app.services.search import normalize_assistant_query


NATURAL_THAI_QUESTION = "จากข้อมูลที่ค้นพบ มีโครงการเกี่ยวกับคอมพิวเตอร์อะไรบ้าง ตอบสั้น ๆ จากข้อมูลที่ให้เท่านั้น"


class RecordingProvider(LLMProvider):
    provider_name = "external-test"
    model_name = "external-test-model"

    def __init__(self) -> None:
        self.answer_calls = 0

    async def generate_summary(self, record: ProcurementRecord) -> str:
        return "summary"

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        self.answer_calls += 1
        return "grounded external answer"


def _add_computer_record(session: Session) -> None:
    session.add(
        ProcurementRecord(
            source_name="fixture",
            dataset_type="synthetic",
            source_record_id="COMPUTER-1",
            content_hash="c" * 64,
            project_name="โครงการจัดซื้อคอมพิวเตอร์",
            agency_name="หน่วยงานตัวอย่าง",
            budget_amount=Decimal("100000"),
            raw_text="จัดซื้อคอมพิวเตอร์สำหรับสำนักงาน",
            normalized_text="จัดซื้อคอมพิวเตอร์สำหรับสำนักงาน",
            is_synthetic=True,
        )
    )
    session.commit()


def _use_synthetic_dataset(monkeypatch) -> None:
    monkeypatch.setenv("DATASET_MODE", "synthetic")
    monkeypatch.setenv("ENABLE_EMBEDDINGS", "false")
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_natural_language_query_normalizes_to_content_term():
    assert normalize_assistant_query(NATURAL_THAI_QUESTION) == "คอมพิวเตอร์"


def test_natural_language_thai_question_retrieves_keyword_evidence(
    client: TestClient,
    session: Session,
    monkeypatch,
):
    _use_synthetic_dataset(monkeypatch)
    _add_computer_record(session)

    response = client.post("/api/assistant/ask", json={"question": NATURAL_THAI_QUESTION, "limit": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["retrieved_records"]
    assert body["citations"]
    assert body["retrieved_records"][0]["source_record_id"] == "COMPUTER-1"


def test_empty_retrieval_never_invokes_external_provider(
    client: TestClient,
    session: Session,
    monkeypatch,
):
    _use_synthetic_dataset(monkeypatch)
    provider = RecordingProvider()
    factory_calls = 0

    def fake_factory(settings):
        nonlocal factory_calls
        factory_calls += 1
        return provider

    monkeypatch.setattr("app.routers.assistant.get_llm_provider", fake_factory)

    response = client.post("/api/assistant/ask", json={"question": "unsupported allegation", "limit": 5})

    assert response.status_code == 200
    assert factory_calls == 0
    assert provider.answer_calls == 0
    assert response.json()["ai_enabled"] is False
    assert response.json()["answer"] == "Cannot determine from available procurement records."
    assert response.json()["citations"] == []
    assert response.json()["retrieved_records"] == []


def test_successful_external_generation_requires_retrieved_evidence(
    client: TestClient,
    session: Session,
    monkeypatch,
):
    _use_synthetic_dataset(monkeypatch)
    _add_computer_record(session)
    provider = RecordingProvider()

    monkeypatch.setattr("app.routers.assistant.get_llm_provider", lambda settings: provider)

    response = client.post("/api/assistant/ask", json={"question": NATURAL_THAI_QUESTION, "limit": 5})

    assert response.status_code == 200
    assert provider.answer_calls == 1
    assert response.json()["ai_enabled"] is True
    assert response.json()["citations"]
    assert response.json()["retrieved_records"]
    assert response.json()["answer"] == "grounded external answer"


def test_blank_assistant_question_remains_unprocessable(
    client: TestClient,
    monkeypatch,
):
    _use_synthetic_dataset(monkeypatch)

    response = client.post("/api/assistant/ask", json={"question": "   ", "limit": 5})

    assert response.status_code == 422
