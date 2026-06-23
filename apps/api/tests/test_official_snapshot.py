import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.data_sources.egp_contract import EGPContractSnapshot
from app.models import ProcurementRecord
from app.services.ingestion import import_rows
from app.services.normalization import parse_date
from app.services.provenance import validate_snapshot


def test_parses_thai_buddhist_era_abbreviated_date():
    assert parse_date("29 พ.ย. 67").isoformat() == "2024-11-29"


def test_snapshot_checksum_and_approved_domain_are_enforced(tmp_path: Path):
    snapshot = tmp_path / "snapshot.csv"
    snapshot.write_text("รหัสโครงการ,ชื่อโครงการ\nA-1,ซื้อคอมพิวเตอร์\n", encoding="utf-8")
    metadata = {
        "snapshot_id": "fixture",
        "source_name": "DGA EGP contract export",
        "source_organization": "Digital Government Development Agency",
        "source_url": "https://data.go.th/dataset/example",
        "download_url": "https://data.go.th/download/example.csv",
        "retrieved_at": "2026-06-21T00:00:00Z",
        "coverage_start": None,
        "coverage_end": None,
        "license": "Creative Commons Attribution",
        "license_url": None,
        "sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "content_type": "text/csv",
        "record_count_raw": 1,
        "redistribution_status": "permitted",
        "notes": [],
    }

    validate_snapshot(snapshot, metadata)

    metadata["source_url"] = "https://attacker.example/snapshot"
    with pytest.raises(ValueError, match="approved official domain"):
        validate_snapshot(snapshot, metadata)


def test_egp_snapshot_maps_thai_fields_without_vendor_personal_data(tmp_path: Path):
    snapshot = tmp_path / "snapshot.csv"
    snapshot.write_text(
        "รหัสโครงการ,ชื่อโครงการ,ชื่อประเภทโครงการ,ชื่อหน่วยงาน,วิธีจัดซื้อฯ,กลุ่มวิธีจัดซื้อฯ,วันที่ประกาศ,งบประมาณ(บาท),ราคาตกลงซื้อ/จ้าง,วันที่เกิดรายการ,จังหวัด,สถานะโครงการ,วันที่ลงนามสัญญา\n"
        "67119524001,ซื้อวัสดุคอมพิวเตอร์,ซื้อ,หน่วยงานทดสอบ,วิธีการจัดหา,เฉพาะเจาะจง,-,1480,1400,29 พ.ย. 67,กรุงเทพมหานคร,ระหว่างดำเนินการ,29 พ.ย. 67\n",
        encoding="utf-8",
    )

    row = next(EGPContractSnapshot(snapshot).rows())

    assert row["source_record_id"] == "67119524001"
    assert row["project_name"] == "ซื้อวัสดุคอมพิวเตอร์"
    assert row["announcement_date"] == "29 พ.ย. 67"
    assert row["winner_name"] is None
    assert "เลขนิติบุคคล" not in row


def test_official_import_is_idempotent_and_isolated_from_synthetic(session: Session):
    row = {
        "source_record_id": "EGP-1",
        "project_name": "ซื้อวัสดุคอมพิวเตอร์",
        "agency_name": "กรมทดสอบ",
        "budget_amount": "1480",
        "source_url": "https://data.go.th/dataset/example",
        "source_snapshot_id": "fixture",
        "source_license": "Creative Commons Attribution",
        "source_checksum": "a" * 64,
        "mapping_version": "dga-egp-v1",
        "source_retrieved_at": "2026-06-21T00:00:00Z",
    }

    first_run, first = import_rows(session, [row], "dga_egp", dataset_type="official_snapshot")
    second_run, second = import_rows(session, [row], "dga_egp", dataset_type="official_snapshot")

    assert first.inserted_rows == 1
    assert second.unchanged_rows == 1
    assert first_run.snapshot_id == "fixture"
    assert second_run.duplicate_rows == 1
    assert session.scalar(select(func.count(ProcurementRecord.id))) == 1
    record = session.scalar(select(ProcurementRecord))
    assert record is not None
    assert record.dataset_type == "official_snapshot"
    assert record.is_synthetic is False


def test_official_records_with_distinct_source_ids_do_not_collapse(session: Session):
    common = {
        "project_name": "ซื้อวัสดุสำนักงาน",
        "agency_name": "กรมทดสอบ",
        "budget_amount": "1000",
        "source_url": "https://data.go.th/dataset/example",
        "source_snapshot_id": "fixture",
        "source_license": "Creative Commons Attributions",
        "source_checksum": "a" * 64,
        "mapping_version": "dga-egp-v1",
    }

    _, counters = import_rows(
        session,
        [{**common, "source_record_id": "EGP-1"}, {**common, "source_record_id": "EGP-2"}],
        "dga_egp",
        dataset_type="official_snapshot",
    )

    assert counters.inserted_rows == 2


def test_source_identity_is_isolated_by_dataset_mode(session: Session):
    common = {
        "source_record_id": "SHARED-1",
        "project_name": "Official record",
        "agency_name": "Official agency",
        "budget_amount": "1000",
        "source_url": "https://data.go.th/dataset/example",
        "source_snapshot_id": "fixture",
        "source_license": "Creative Commons Attributions",
        "source_checksum": "a" * 64,
        "mapping_version": "dga-egp-v1",
    }
    import_rows(session, [common], "shared_source", dataset_type="official_snapshot")

    import_rows(
        session,
        [{"source_record_id": "SHARED-1", "project_name": "Synthetic record", "agency_name": "Sample agency"}],
        "shared_source",
        dataset_type="synthetic",
    )

    records = session.scalars(select(ProcurementRecord).order_by(ProcurementRecord.dataset_type)).all()
    assert [(record.dataset_type, record.project_name) for record in records] == [
        ("official_snapshot", "Official record"),
        ("synthetic", "Synthetic record"),
    ]


def test_dataset_status_exposes_active_mode_and_quality(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    metadata_path = tmp_path / "metadata.json"
    quality_path = tmp_path / "quality.json"
    metadata_path.write_text(
        json.dumps(
            {
                "snapshot_id": "fixture",
                "source_name": "DGA EGP contract export",
                "source_organization": "Digital Government Development Agency",
                "source_url": "https://data.go.th/dataset/example",
                "download_url": "https://data.go.th/download/example.csv",
                "retrieved_at": "2026-06-21T00:00:00Z",
                "coverage_start": "2024-10-01",
                "coverage_end": "2024-12-31",
                "license": "Creative Commons Attribution",
                "license_url": None,
                "sha256": "a" * 64,
                "content_type": "text/csv",
                "record_count_raw": 250,
                "redistribution_status": "permitted",
                "notes": [],
                "mapping_version": "dga-egp-v1",
            }
        ),
        encoding="utf-8",
    )
    quality_path.write_text(json.dumps({"valid_records": 249, "rejected_records": 1, "duplicate_records": 0}), encoding="utf-8")
    monkeypatch.setenv("DATASET_MODE", "official_snapshot")
    monkeypatch.setenv("OFFICIAL_SNAPSHOT_METADATA", str(metadata_path))
    monkeypatch.setenv("OFFICIAL_QUALITY_REPORT", str(quality_path))
    get_settings.cache_clear()

    response = client.get("/api/dataset/status")

    assert response.status_code == 200
    assert response.json()["dataset_mode"] == "official_snapshot"
    assert response.json()["quality"]["valid_records"] == 249
    get_settings.cache_clear()


def test_dataset_status_resolves_bundled_evidence_outside_process_directory(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATASET_MODE", "official_snapshot")
    monkeypatch.setenv("OFFICIAL_SNAPSHOT_METADATA", "data/official/metadata/dga-egp-contract-2568-250.json")
    monkeypatch.setenv("OFFICIAL_QUALITY_REPORT", "reports/official_snapshot/data_quality_summary.json")
    get_settings.cache_clear()

    response = client.get("/api/dataset/status")

    assert response.status_code == 200
    assert response.json()["source"]["snapshot_id"] == "dga-egp-contract-2568-250"
    assert response.json()["quality"]["checksum_verified"] is True
    get_settings.cache_clear()


def test_public_ingestion_requires_admin_token(client: TestClient):
    response = client.post("/api/ingestion/import-csv", files={"file": ("records.csv", b"project_name\nunsafe")})

    assert response.status_code == 403
