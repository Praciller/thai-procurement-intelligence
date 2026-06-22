from sqlalchemy.orm import Session

from app.services.ingestion import import_rows


def test_csv_export_escapes_formula_cells(client, session: Session):
    import_rows(
        session,
        [
            {
                "source_record_id": "F-1",
                "project_name": "=HYPERLINK(\"bad\")",
                "agency_name": "+unsafe",
                "province": "@unsafe",
                "procurement_method": "-unsafe",
            }
        ],
        "unit",
    )

    response = client.get("/api/export/records.csv")

    assert response.status_code == 200
    assert "'=HYPERLINK" in response.text
    assert "'+unsafe" in response.text
    assert "'@Unsafe" in response.text
    assert "'-unsafe" in response.text
