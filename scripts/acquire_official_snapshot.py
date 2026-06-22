from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


DOWNLOAD_URL = "https://data.go.th/dataset/3beb7813-3607-4e5f-a094-b3b574a6e358/resource/35961821-d945-4fc0-8ce1-a96b4cd46bd6/download/2568-egp-contract-10.csv"
SOURCE_URL = "https://data.go.th/dataset/3beb7813-3607-4e5f-a094-b3b574a6e358"
SAFE_FIELDS = [
    "ลำดับ",
    "รหัสโครงการ",
    "ชื่อโครงการ",
    "ชื่อประเภทโครงการ",
    "ชื่อหน่วยงาน",
    "ชื่อหน่วยงานย่อย",
    "วิธีจัดซื้อฯ",
    "กลุ่มวิธีจัดซื้อฯ",
    "วันที่ประกาศ",
    "งบประมาณ(บาท)",
    "ราคากลาง(บาท)",
    "ราคาตกลงซื้อ/จ้าง",
    "ปีงบประมาณ",
    "วันที่เกิดรายการ",
    "จังหวัด",
]


class ApprovedDomainRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname != "data.go.th":
            raise ValueError("unapproved download domain")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def acquire(destination: Path, metadata_path: Path, limit: int, retrieved_at: str | None = None) -> dict:
    parsed_download = urlparse(DOWNLOAD_URL)
    if parsed_download.scheme != "https" or parsed_download.hostname != "data.go.th":
        raise ValueError("unapproved download domain")
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"Range": "bytes=0-1048575", "User-Agent": "thai-procurement-intelligence/1.0"},
    )
    with urllib.request.build_opener(ApprovedDomainRedirectHandler()).open(request, timeout=60) as response:
        content_type = response.headers.get_content_type()
        upstream_last_modified = response.headers.get("Last-Modified")
        upstream_etag = response.headers.get("ETag")
        body = response.read(1_048_577)
    if content_type not in {"text/csv", "application/csv", "application/octet-stream"}:
        raise ValueError(f"unexpected content type: {content_type}")
    if len(body) > 1_048_576:
        raise ValueError("download exceeded 1 MiB acquisition limit")

    complete_body = body.rsplit(b"\n", 1)[0] + b"\n"
    text = complete_body.decode("utf-8-sig")
    rows = []
    seen = set()
    for row in csv.DictReader(io.StringIO(text)):
        record_id = (row.get("รหัสโครงการ") or "").strip()
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        rows.append({field: row.get(field, "") for field in SAFE_FIELDS})
        if len(rows) == limit:
            break
    if len(rows) != limit:
        raise ValueError(f"expected {limit} records, found {len(rows)}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=SAFE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    timestamp = retrieved_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    metadata = {
        "snapshot_id": "dga-egp-contract-2568-250",
        "source_name": "Thailand Government Spending EGP contract export FY2568",
        "source_organization": "Digital Government Development Agency (Public Organization), sourced with Comptroller General's Department cooperation",
        "source_url": SOURCE_URL,
        "download_url": DOWNLOAD_URL,
        "retrieved_at": timestamp,
        "coverage_start": None,
        "coverage_end": None,
        "license": "Creative Commons Attributions",
        "license_url": None,
        "sha256": digest,
        "content_type": "text/csv",
        "record_count_raw": len(rows),
        "redistribution_status": "permitted",
        "mapping_version": "dga-egp-v1",
        "source_updated_at": "2026-05-11T04:59:38.290911Z",
        "notes": [
            "Bounded first-250 unique-project subset from resource part 10; not representative of all Thai procurement.",
            "Vendor names and legal/tax identifiers were excluded because they are unnecessary for this case study.",
            "Columns after province were excluded because upstream rows do not consistently preserve empty columns, causing positional shifts.",
            f"Upstream Last-Modified: {upstream_last_modified}",
            f"Upstream ETag: {upstream_etag}",
        ],
    }
    dates = []
    for row in rows:
        raw = row.get("วันที่เกิดรายการ", "")
        if raw:
            dates.append(raw)
    metadata["notes"].append(f"Observed upstream date labels: {min(dates)} through {max(dates)} (Thai display format; lexical range only).")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire the approved bounded DGA EGP snapshot.")
    parser.add_argument("--output", type=Path, default=Path("data/official/raw/dga-egp-contract-2568-250.csv"))
    parser.add_argument("--metadata", type=Path, default=Path("data/official/metadata/dga-egp-contract-2568-250.json"))
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--retrieved-at")
    args = parser.parse_args()
    metadata = acquire(args.output, args.metadata, args.limit, args.retrieved_at)
    print(json.dumps({"snapshot_id": metadata["snapshot_id"], "records": metadata["record_count_raw"], "sha256": metadata["sha256"]}))


if __name__ == "__main__":
    main()
