from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.data_sources.base import DataSource


class ExcelDataSource(DataSource):
    def __init__(self, path: str | Path, source_name: str = "excel"):
        self.path = Path(path)
        self.source_name = source_name

    def rows(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError("Excel import is a documented extension point for the MVP.")

