import hashlib
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import ProcurementEmbedding, ProcurementRecord
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.provider_config import ProviderConfig
from app.services.llm.router import ProviderEntry, ProviderRouter


class CountingProvider(LLMProvider):
    provider_name = "test-provider"
    model_name = "test-model"

    def __init__(self) -> None:
        self.summary_calls = 0
        self.answer_calls = 0

    async def generate_summary(self, record: ProcurementRecord) -> str:
        self.summary_calls += 1
        return f"Summary call {self.summary_calls}: {record.project_name}"

    async def answer_question(self, question: str, records: list[ProcurementRecord]) -> str:
        self.answer_calls += 1
        return "Answer based on retrieved records"


def _config() -> ProviderConfig:
    return ProviderConfig(
        name="test-provider",
        api_style="mock",
        base_url=None,
        api_key_env=None,
        model="test-model",
        timeout=1,
        max_retries=0,
        enabled=True,
        automatic_fallback_allowed=True,
        deterministic_evaluation_allowed=True,
    )


def _record(source_record_id: str, *, dataset_type: str = "synthetic", raw_text: str = "target evidence") -> ProcurementRecord:
    return ProcurementRecord(
        source_name="hardening-fixture",
        dataset_type=dataset_type,
        source_record_id=source_record_id,
        content_hash=hashlib.sha256(source_record_id.encode()).hexdigest(),
        project_name=f"Project {source_record_id}",
        agency_name="Fixture agency",
        province="Fixture province",
        procurement_method="e-bidding",
        procurement_category="IT",
        budget_amount=Decimal("1000"),
        announcement_date=date(2025, 1, 1),
        raw_text=raw_text,
        normalized_text=raw_text,
        is_synthetic=dataset_type == "synthetic",
    )


def _seed_ranked(session: Session, count: int = 5) -> list[ProcurementRecord]:
    records = [_record(f"R-{index:02d}") for index in range(count)]
    session.add_all(records)
    session.flush()
    session.add_all(
        [
            ProcurementEmbedding(
                procurement_id=record.id,
                embedding_model="fixture",
                embedding=[1.0, 0.0],
                embedded_text=record.project_name,
                text_hash=hashlib.sha256(record.project_name.encode()).hexdigest(),
            )
            for record in records
        ]
    )
    session.commit()
    return records


@pytest.fixture(autouse=True)
def synthetic_dataset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATASET_MODE", "synthetic")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("search_mode", ["semantic", "hybrid"])
def test_ranked_records_paginate_over_the_full_sorted_result_set(
    client: TestClient,
    session: Session,
    search_mode: str,
):
    _seed_ranked(session)

    first = client.get(f"/api/records?q=target&search_mode={search_mode}&page=1&page_size=2")
    second = client.get(f"/api/records?q=target&search_mode={search_mode}&page=2&page_size=2")

    assert first.status_code == second.status_code == 200
    assert first.json()["total"] == second.json()["total"] == 5
    assert [item["source_record_id"] for item in first.json()["items"]] == ["R-00", "R-01"]
    assert [item["source_record_id"] for item in second.json()["items"]] == ["R-02", "R-03"]


def test_record_facets_include_values_after_page_one_and_isolate_dataset_mode(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    synthetic = [
        _record(
            f"S-{index:02d}",
        )
        for index in range(21)
    ]
    for index, record in enumerate(synthetic):
        record.province = f"Province {index:02d}"
        record.procurement_category = f"Category {index:02d}"
    session.add_all(synthetic)
    session.add(_record("OFFICIAL-1", dataset_type="official_snapshot"))
    session.commit()

    response = client.get("/api/records/facets")

    assert response.status_code == 200
    assert response.json()["provinces"][0] == "Province 00"
    assert response.json()["provinces"][-1] == "Province 20"
    assert response.json()["categories"][-1] == "Category 20"
    assert len(response.json()["provinces"]) == 21

    monkeypatch.setenv("DATASET_MODE", "official_snapshot")
    get_settings.cache_clear()
    official = client.get("/api/records/facets")

    assert official.status_code == 200
    assert official.json()["provinces"] == ["Fixture province"]
    assert official.json()["categories"] == ["IT"]


def test_ranked_search_rejects_unsupported_sort_and_excessive_window(client: TestClient):
    unsupported_sort = client.get("/api/records?q=target&search_mode=hybrid&sort=date_desc")
    unsupported_mode_sort = client.get("/api/records?q=target&sort=unsupported")
    excessive_window = client.get("/api/records?q=target&search_mode=semantic&page=251&page_size=20")

    assert unsupported_sort.status_code == 422
    assert unsupported_mode_sort.status_code == 422
    assert excessive_window.status_code == 422


def test_assistant_rejects_oversized_or_unknown_filters(client: TestClient):
    oversized_question = client.post("/api/assistant/ask", json={"question": "x" * 501})
    oversized_filter = client.post("/api/assistant/ask", json={"question": "target", "filters": {"province": "x" * 121}})
    unknown_filter = client.post("/api/assistant/ask", json={"question": "target", "filters": {"debug": "true"}})

    assert oversized_question.status_code == 422
    assert oversized_filter.status_code == 422
    assert unknown_filter.status_code == 422


def test_no_evidence_returns_deterministic_answer_without_provider_selection(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    settings = Settings(_env_file=None, enable_llm=True, enable_embeddings=True)

    def reject_provider_selection(current_settings):
        raise AssertionError("no evidence must not select or call an LLM provider")

    monkeypatch.setattr("app.routers.assistant.get_settings", lambda: settings)
    monkeypatch.setattr("app.routers.assistant.get_llm_provider", reject_provider_selection)

    response = client.post("/api/assistant/ask", json={"question": "target"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Cannot determine from available procurement records."
    assert response.json()["ai_enabled"] is False
    assert response.json()["citations"] == []


def test_enabled_provider_router_reuses_only_current_prompt_summaries(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    settings = Settings(_env_file=None, enable_llm=True)
    provider = CountingProvider()
    record = _record("CACHE-1")
    session.add(record)
    session.commit()

    monkeypatch.setattr("app.routers.records.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.routers.records.get_llm_provider",
        lambda current_settings: ProviderRouter([ProviderEntry(_config(), provider)]),
    )

    first = client.post(f"/api/records/{record.id}/summary")
    second = client.post(f"/api/records/{record.id}/summary")
    record.raw_text = "changed source text"
    record.normalized_text = "changed source text"
    record.procurement_category = "Construction"
    session.commit()
    changed = client.post(f"/api/records/{record.id}/summary")

    assert first.status_code == second.status_code == changed.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert second.json()["provider"] == "test-provider"
    assert changed.json()["cached"] is False
    assert provider.summary_calls == 2
    assert session.scalar(select(ProcurementRecord).where(ProcurementRecord.id == record.id)).content_hash == record.content_hash


def test_disabled_mock_path_does_not_use_the_external_rate_limit(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    record = _record("MOCK-1")
    session.add(record)
    session.commit()
    settings = Settings(_env_file=None, enable_llm=False)

    def reject_rate_limit(*args, **kwargs):
        raise AssertionError("mock inference must not claim an external rate-limit slot")

    monkeypatch.setattr("app.routers.assistant.get_settings", lambda: settings)
    monkeypatch.setattr("app.routers.assistant.get_llm_provider", lambda current_settings: MockLLMProvider())
    monkeypatch.setattr("app.services.llm.limits.claim_external_llm_request", reject_rate_limit)

    response = client.post("/api/assistant/ask", json={"question": "target"})

    assert response.status_code == 200
    assert response.json()["ai_enabled"] is False


def test_assistant_and_summary_share_a_per_ip_external_call_limit(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.services import rate_limit

    record = _record("RATE-1")
    session.add(record)
    session.commit()
    provider = CountingProvider()
    settings = Settings(_env_file=None, enable_llm=True)
    rate_limit._requests.pop("testclient", None)
    monkeypatch.setattr(rate_limit, "MAX_EXTERNAL_LLM_REQUESTS_PER_IP_PER_MINUTE", 1)
    monkeypatch.setattr("app.routers.assistant.get_settings", lambda: settings)
    monkeypatch.setattr("app.routers.records.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.routers.assistant.get_llm_provider",
        lambda current_settings: ProviderRouter([ProviderEntry(_config(), provider)]),
    )
    monkeypatch.setattr(
        "app.routers.records.get_llm_provider",
        lambda current_settings: ProviderRouter([ProviderEntry(_config(), provider)]),
    )

    answer = client.post(
        "/api/assistant/ask",
        json={"question": "target"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )
    blocked_summary = client.post(
        f"/api/records/{record.id}/summary",
        headers={"X-Forwarded-For": "198.51.100.7"},
    )

    assert answer.status_code == 200
    assert blocked_summary.status_code == 429
    assert int(blocked_summary.headers["Retry-After"]) > 0
    assert provider.answer_calls == 1
    assert provider.summary_calls == 0


def test_summary_input_limit_blocks_oversized_provider_context(
    client: TestClient,
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
):
    provider = CountingProvider()
    record = _record("LARGE-1", raw_text="x" * 25_000)
    session.add(record)
    session.commit()
    settings = Settings(_env_file=None, enable_llm=True)
    monkeypatch.setattr("app.routers.records.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.routers.records.get_llm_provider",
        lambda current_settings: ProviderRouter([ProviderEntry(_config(), provider)]),
    )

    response = client.post(f"/api/records/{record.id}/summary")

    assert response.status_code == 413
    assert provider.summary_calls == 0
