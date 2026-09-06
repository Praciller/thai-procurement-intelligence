import ipaddress
import socket
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

import httpx

from app.data_sources.base import DataSource

_ALLOWED_SCHEMES = {"http", "https"}


def _validated_public_url(url: str) -> tuple[str, str]:
    """Validate an operator-supplied ingestion URL before any request is made.

    Returns the scheme-checked URL and its resolved public host IP. Rejects
    loopback, private, link-local, and reserved addresses (including cloud
    metadata endpoints) so the CLI cannot be pointed at internal targets.
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError("Source URL must be an absolute http(s) URL with a host")
    try:
        resolved = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as exc:
        raise ValueError(f"Source URL host could not be resolved: {parsed.hostname}") from exc
    for candidate in resolved:
        address = ipaddress.ip_address(candidate)
        if not address.is_global:
            raise ValueError(
                f"Source URL host resolves to a non-public address ({candidate}); "
                "refusing to fetch it"
            )
    return url, parsed.hostname


def _fetch_public_json(url: str) -> Any:
    safe_url, _host = _validated_public_url(url)
    # Redirects stay off so a validated origin cannot bounce the fetch onto a
    # private target; the URL is re-validated on every call to narrow the
    # DNS-rebinding window.
    _validated_public_url(safe_url)
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.get(safe_url, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()


class OpenApiDataSource(DataSource):
    def __init__(self, url: str, source_name: str = "open_api"):
        _validated_public_url(url)
        self.url = url
        self.source_name = source_name

    def rows(self) -> Iterable[dict[str, Any]]:
        data = _fetch_public_json(self.url)
        if isinstance(data, list):
            yield from data
            return
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            yield from data["items"]
            return
        raise ValueError("Unsupported API response shape")
