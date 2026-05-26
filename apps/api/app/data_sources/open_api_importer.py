from collections.abc import Iterable
from typing import Any

import httpx

from app.data_sources.base import DataSource


class OpenApiDataSource(DataSource):
    def __init__(self, url: str, source_name: str = "open_api"):
        self.url = url
        self.source_name = source_name

    def rows(self) -> Iterable[dict[str, Any]]:
        response = httpx.get(self.url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            yield from data
            return
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            yield from data["items"]
            return
        raise ValueError("Unsupported API response shape")

