"""SSRF guard tests for the open-API ingestion client."""

from __future__ import annotations

import socket

import pytest

from app.data_sources.open_api_importer import OpenApiDataSource, _validated_public_url

_PUBLIC_ADDRINFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/api/records",
        "http://localhost/api/records",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.5/items",
        "http://192.168.1.10/items",
        "file:///etc/passwd",
        "ftp://example.org/data",
        "not-a-url",
    ],
)
def test_non_public_or_invalid_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        _validated_public_url(url)
    with pytest.raises(ValueError):
        OpenApiDataSource(url)


def test_public_url_is_accepted_and_stored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: _PUBLIC_ADDRINFO)
    source = OpenApiDataSource("https://data.go.th/example.json", source_name="dga")
    assert source.url == "https://data.go.th/example.json"
    assert source.source_name == "dga"
