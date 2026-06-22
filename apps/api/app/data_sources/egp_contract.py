from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.data_sources.base import DataSource


class EGPContractSnapshot(DataSource):
    source_name = "dga_egp_contract_2568"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def rows(self) -> Iterable[dict[str, Any]]:
        with self.path.open("r", encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                announcement = row.get("วันที่ประกาศ")
                if not announcement or announcement.strip() == "-":
                    announcement = row.get("วันที่เกิดรายการ")
                yield {
                    "source_record_id": row.get("รหัสโครงการ"),
                    "project_name": row.get("ชื่อโครงการ"),
                    "agency_name": row.get("ชื่อหน่วยงาน"),
                    "province": row.get("จังหวัด"),
                    "procurement_method": row.get("กลุ่มวิธีจัดซื้อฯ") or row.get("วิธีจัดซื้อฯ"),
                    "procurement_category": row.get("ชื่อประเภทโครงการ"),
                    "budget_amount": row.get("งบประมาณ(บาท)"),
                    "winning_amount": row.get("ราคาตกลงซื้อ/จ้าง"),
                    "winner_name": None,
                    "announcement_date": announcement,
                    "contract_date": None,
                    "raw_text": None,
                }
