import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.data_sources.base import DataSource


class CsvDataSource(DataSource):
    def __init__(self, path: str | Path, source_name: str = "csv"):
        self.path = Path(path)
        self.source_name = source_name

    def rows(self) -> Iterable[dict[str, Any]]:
        with self.path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            yield from csv.DictReader(csv_file)

