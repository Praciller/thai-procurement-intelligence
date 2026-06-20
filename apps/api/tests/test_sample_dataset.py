import csv
from pathlib import Path


SAMPLE_CSV = Path(__file__).parents[3] / "data" / "sample" / "procurement_sample.csv"


def test_committed_sample_is_clearly_synthetic():
    with SAMPLE_CSV.open(encoding="utf-8-sig", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 120
    assert all(row["agency_name"].startswith("Sample ") for row in rows)
    assert all(not row["winner_name"] or row["winner_name"].startswith("Sample ") for row in rows)
    assert all(row["source_url"].startswith("https://example.org/") for row in rows)
