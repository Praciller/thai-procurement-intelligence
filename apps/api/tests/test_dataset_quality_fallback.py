"""Dataset status must distinguish stored provenance from byte-level verification."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ProcurementRecord


@pytest.mark.parametrize("same_checksum", [True, False])
def test_missing_quality_artifact_never_claims_verified_source_bytes(
    client, session: Session, monkeypatch: pytest.MonkeyPatch, same_checksum: bool
):
    monkeypatch.setenv("DATASET_MODE", "official_snapshot")
    monkeypatch.setenv("OFFICIAL_SNAPSHOT_METADATA", "unavailable-provenance-metadata.json")
    monkeypatch.setenv("OFFICIAL_QUALITY_REPORT", "unavailable-quality-artifact.json")
    get_settings.cache_clear()
    try:
        for index, checksum in enumerate(("a" * 64, "a" * 64 if same_checksum else "b" * 64), start=1):
            session.add(
                ProcurementRecord(
                    source_name="official",
                    dataset_type="official_snapshot",
                    source_record_id=f"SRC-{index}",
                    source_snapshot_id="official-test-snapshot",
                    source_retrieved_at=datetime(2026, 6, 21, tzinfo=UTC),
                    source_url="https://data.go.th/dataset/test",
                    source_license="CC Attribution",
                    source_checksum=checksum,
                    mapping_version="1",
                    content_hash=(str(index) * 64),
                    project_name=f"Project {index}",
                    is_synthetic=False,
                )
            )
        session.commit()
        response = client.get("/api/dataset/status")
        assert response.status_code == 200
        body = response.json()
        assert body["dataset_mode"] == "official_snapshot"
        assert body["source"]["record_count_raw"] == 2
        assert body["quality"]["checksum_verified"] is False
        assert body["quality"]["stored_provenance_consistent"] is same_checksum
        assert "not rehashed" in body["quality"]["verification_note"]
    finally:
        get_settings.cache_clear()
