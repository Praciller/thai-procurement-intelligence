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


def test_semantic_search_rejects_whitespace_query(client: TestClient):
    response = client.post("/api/search/semantic", json={"query": "   ", "limit": 5})

    assert response.status_code == 422


def test_assistant_rejects_whitespace_question(client: TestClient):
    response = client.post("/api/assistant/ask", json={"question": "   ", "limit": 4})

    assert response.status_code == 422


def test_records_semantic_mode_treats_whitespace_as_no_query(client: TestClient, session: Session):
    seed(session)

    response = client.get("/api/records?search_mode=semantic&q=%20%20%20")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["relevance_score"] is None for item in data["items"])


def test_summary_cache_invalidates_when_record_content_changes(client: TestClient, session: Session):
    seed(session)
    record_id = client.get("/api/records?q=cybersecurity").json()["items"][0]["id"]
    initial = client.post(f"/api/records/{record_id}/summary")
    assert initial.status_code == 200
    assert initial.json()["cached"] is False

    record = session.get(ProcurementRecord, record_id)
    record.content_hash = "b" * 64
    session.commit()

    # Record details must not surface an outdated summary before regeneration.
    details = client.get(f"/api/records/{record_id}")
    assert details.status_code == 200
    assert details.json()["ai_summary"] is None

    refreshed = client.post(f"/api/records/{record_id}/summary")
    assert refreshed.status_code == 200
    assert refreshed.json()["cached"] is False
    assert client.post(f"/api/records/{record_id}/summary").json()["cached"] is True


def test_summary_cache_hits_with_primary_router_provider(client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch):
    from app.services.llm.mock import MockLLMProvider
    from app.services.llm.provider_config import ProviderConfig
    from app.services.llm.router import ProviderEntry, ProviderRouter

    seed(session)
    record_id = client.get("/api/records?q=cybersecurity").json()["items"][0]["id"]

    class CountingProvider(MockLLMProvider):
        provider_name = "fixture-primary"
        model_name = "fixture-model"

        def __init__(self):
            self.summary_calls = 0

        async def generate_summary(self, record):
            self.summary_calls += 1
            return await super().generate_summary(record)

    provider = CountingProvider()
    config = ProviderConfig(
        name="fixture-primary", api_style="mock", base_url=None, api_key_env=None,
        model="fixture-model", timeout=0, max_retries=0,
        enabled=True, automatic_fallback_allowed=True, deterministic_evaluation_allowed=True,
    )
    monkeypatch.setattr(
        "app.routers.records.get_llm_provider",
        lambda settings: ProviderRouter([ProviderEntry(config, provider)]),
    )

    first = client.post(f"/api/records/{record_id}/summary")
    second = client.post(f"/api/records/{record_id}/summary")

    assert first.status_code == second.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert first.json()["provider"] == "fixture-primary"
    assert provider.summary_calls == 1


@pytest.mark.parametrize("endpoint,payload", [
    ("/api/assistant/ask", {"question": "a" * 1001}),
    ("/api/search/semantic", {"query": "a" * 1001}),
])
def test_text_search_endpoints_reject_oversized_input(client: TestClient, endpoint: str, payload: dict):
    response = client.post(endpoint, json=payload)
    assert response.status_code == 422


def test_records_reject_oversized_query(client: TestClient):
    response = client.get("/api/records", params={"q": "a" * 1001})
    assert response.status_code == 422


def test_keyword_search_pagination(client: TestClient, session: Session):
    seed(session)
    first = client.get("/api/records", params={"page": 1, "page_size": 1})
    second = client.get("/api/records", params={"page": 2, "page_size": 1})
    assert first.status_code == second.status_code == 200
    assert first.json()["total"] == second.json()["total"] == 2
    assert first.json()["items"][0]["id"] != second.json()["items"][0]["id"]



def test_record_facets_cover_entire_active_dataset_not_just_first_page(client: TestClient, session: Session):
    seed(session)
    first_page = client.get("/api/records", params={"page_size": 1})
    facets = client.get("/api/records/facets")

    assert first_page.status_code == facets.status_code == 200
    assert len(first_page.json()["items"]) == 1
    assert facets.json() == {
        "provinces": ["Bangkok", "Chiang Mai"],
        "categories": ["Construction", "IT"],
    }


def test_record_facets_exclude_records_in_inactive_dataset(client: TestClient, session: Session):
    seed(session)
    import_rows(
        session,
        [{
            "source_record_id": "OFF-1",
            "project_name": "Official evidence",
            "agency_name": "Official agency",
            "province": "Surin",
            "procurement_category": "Official only",
            "source_url": "https://data.go.th/dataset/example",
            "source_snapshot_id": "fixture",
            "source_license": "Creative Commons Attribution",
            "source_checksum": "a" * 64,
            "mapping_version": "v1",
        }],
        "official",
        dataset_type="official_snapshot",
    )

    response = client.get("/api/records/facets")
    assert response.status_code == 200
    assert "Surin" not in response.json()["provinces"]
    assert "Official only" not in response.json()["categories"]



@pytest.mark.parametrize("mode", ["semantic", "hybrid"])
def test_ranked_modes_reject_unimplemented_page_two(client: TestClient, session: Session, mode: str):
    seed(session)
    response = client.get("/api/records", params={
        "q": "cybersecurity", "search_mode": mode, "page": 2,
    })
    assert response.status_code == 422
    assert "pagination" in response.json()["detail"].lower()


def test_local_semantic_routes_do_not_return_unrelated_hash_collisions(
    client: TestClient, session: Session
):
    seed(session)
    question = "ดาวเทียมสำรวจอวกาศ"
    post = client.post("/api/search/semantic", json={"query": question, "limit": 5})
    get = client.get("/api/records", params={
        "search_mode": "semantic", "q": question,
    })
    assert post.status_code == 200
    assert post.json() == []
    assert get.status_code == 200
    assert get.json()["items"] == []
    assert get.json()["total"] == 0


def test_local_semantic_search_preserves_supported_keyword_evidence(
    client: TestClient, session: Session
):
    seed(session)
    post = client.post("/api/search/semantic", json={"query": "cybersecurity"})
    get = client.get("/api/records", params={
        "search_mode": "semantic", "q": "cybersecurity",
    })
    assert post.status_code == get.status_code == 200
    assert len(post.json()) == get.json()["total"] == 1
    assert post.json()[0]["procurement_category"] == "IT"
    assert get.json()["items"][0]["procurement_category"] == "IT"



def test_records_search_does_not_expand_raw_sql_like_metacharacters(
    client: TestClient, session: Session
):
    seed(session)
    for query in ("%", "_"):
        response = client.get("/api/records", params={"q": query})
        assert response.status_code == 200
        assert response.json()["items"] == []
        assert response.json()["total"] == 0



def test_embedding_write_requires_explicit_admin_token(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
):
    from types import SimpleNamespace

    from app.models import ProcurementEmbedding

    import_rows(session, [{"source_record_id": "AUTH-1", "project_name": "Authorized embedding fixture"}], "unit")
    record = session.scalar(select(ProcurementRecord).where(ProcurementRecord.source_record_id == "AUTH-1"))
    assert record is not None
    url = f"/api/records/{record.id}/embedding"

    # The endpoint is disabled unless a server-side token is configured.
    monkeypatch.setattr(
        "app.routers.records.get_settings",
        lambda: SimpleNamespace(dataset_mode="synthetic", admin_ingestion_token=None),
    )
    assert client.post(url).status_code == 403
    assert client.post(url, headers={"X-Admin-Token": "invented"}).status_code == 403

    # Incorrect and absent headers must never persist an embedding.
    monkeypatch.setattr(
        "app.routers.records.get_settings",
        lambda: SimpleNamespace(dataset_mode="synthetic", admin_ingestion_token="unit-test-token"),
    )
    assert client.post(url).status_code == 403
    assert client.post(url, headers={"X-Admin-Token": "incorrect"}).status_code == 403
    assert session.scalar(
        select(ProcurementEmbedding).where(ProcurementEmbedding.procurement_id == record.id)
    ) is None

    permitted = client.post(url, headers={"X-Admin-Token": "unit-test-token"})
    repeated = client.post(url, headers={"X-Admin-Token": "unit-test-token"})
    assert permitted.status_code == repeated.status_code == 200
    assert permitted.json()["model"] == "hashing-token-v1"
    assert permitted.json()["id"] == repeated.json()["id"]
    assert len(session.scalars(
        select(ProcurementEmbedding).where(ProcurementEmbedding.procurement_id == record.id)
    ).all()) == 1
