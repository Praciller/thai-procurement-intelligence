from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


APPROVED_OFFICIAL_DOMAINS = {"data.go.th"}


def validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in APPROVED_OFFICIAL_DOMAINS:
        raise ValueError("source URL must use an approved official domain")


def validate_snapshot(path: Path, metadata: dict) -> None:
    validate_official_url(metadata["source_url"])
    if metadata.get("download_url"):
        validate_official_url(metadata["download_url"])
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != metadata["sha256"]:
        raise ValueError("snapshot checksum mismatch")


def read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def freshness_status(retrieved_at: str | None) -> str:
    if not retrieved_at:
        return "unknown"
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    age_days = (datetime.now(UTC) - retrieved).days
    return "current_snapshot" if age_days <= 90 else "stale_snapshot"
