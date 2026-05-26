from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime


_ai_calls: dict[str, int] = defaultdict(int)


def check_hourly_ai_limit(limit: int, bucket: str = "global") -> bool:
    if limit <= 0:
        return False
    hour_key = datetime.now(UTC).strftime("%Y%m%d%H")
    key = f"{bucket}:{hour_key}"
    if _ai_calls[key] >= limit:
        return False
    _ai_calls[key] += 1
    return True

