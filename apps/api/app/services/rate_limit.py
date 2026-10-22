from __future__ import annotations

from collections import deque
from math import ceil
from threading import Lock
from time import monotonic


WINDOW_SECONDS = 60.0
MAX_EXTERNAL_LLM_REQUESTS_PER_IP_PER_MINUTE = 5
MAX_TRACKED_CLIENTS = 10_000

_requests: dict[str, deque[float]] = {}
_last_cleanup = 0.0
_lock = Lock()


def claim_external_llm_request(client_ip: str, *, now: float | None = None) -> int | None:
    """Return retry seconds when this process has reached the client's limit."""
    global _last_cleanup

    current = monotonic() if now is None else now
    client = client_ip or "unknown"
    with _lock:
        if current - _last_cleanup >= WINDOW_SECONDS:
            for tracked_ip, timestamps in tuple(_requests.items()):
                while timestamps and timestamps[0] <= current - WINDOW_SECONDS:
                    timestamps.popleft()
                if not timestamps:
                    del _requests[tracked_ip]
            _last_cleanup = current

        timestamps = _requests.get(client)
        if timestamps is None:
            if len(_requests) >= MAX_TRACKED_CLIENTS:
                return ceil(WINDOW_SECONDS)
            timestamps = _requests[client] = deque()

        while timestamps and timestamps[0] <= current - WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= MAX_EXTERNAL_LLM_REQUESTS_PER_IP_PER_MINUTE:
            return max(1, ceil(WINDOW_SECONDS - (current - timestamps[0])))

        timestamps.append(current)
        return None
