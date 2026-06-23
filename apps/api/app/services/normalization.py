from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


THAI_PROVINCE_ALIASES = {
    "bangkok": "Bangkok",
    "bkk": "Bangkok",
    "กรุงเทพ": "Bangkok",
    "กรุงเทพฯ": "Bangkok",
    "chiang mai": "Chiang Mai",
    "เชียงใหม่": "Chiang Mai",
    "phuket": "Phuket",
    "ภูเก็ต": "Phuket",
    "khon kaen": "Khon Kaen",
    "ขอนแก่น": "Khon Kaen",
    "chonburi": "Chonburi",
    "ชลบุรี": "Chonburi",
    "songkhla": "Songkhla",
    "สงขลา": "Songkhla",
}


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return re.sub(r"\s+", " ", text)


def normalize_province(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    return THAI_PROVINCE_ALIASES.get(text.casefold(), text.title() if text.isascii() else text)


def normalize_agency(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    return text


def parse_decimal(value: Any) -> Decimal | None:
    text = clean_text(value)
    if not text or text.lower() in {"nan", "none", "null", "-"}:
        return None
    normalized = re.sub(r"[^\d.\-]", "", text)
    if normalized in {"", ".", "-"}:
        return None
    try:
        return Decimal(normalized).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc


def parse_date(value: Any) -> date | None:
    text = clean_text(value)
    if not text or text.lower() in {"nan", "none", "null", "-"}:
        return None

    thai_months = {
        "ม.ค.": 1,
        "ก.พ.": 2,
        "มี.ค.": 3,
        "เม.ย.": 4,
        "พ.ค.": 5,
        "มิ.ย.": 6,
        "ก.ค.": 7,
        "ส.ค.": 8,
        "ก.ย.": 9,
        "ต.ค.": 10,
        "พ.ย.": 11,
        "ธ.ค.": 12,
    }
    match = re.fullmatch(r"(\d{1,2})\s+([^\s]+)\s+(\d{2,4})", text)
    if match and match.group(2) in thai_months:
        year = int(match.group(3))
        year = year + 2500 if year < 100 else year
        year = year - 543 if year > 2400 else year
        return date(year, thai_months[match.group(2)], int(match.group(1)))

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year > 2400:
                parsed = parsed.replace(year=parsed.year - 543)
            return parsed
        except ValueError:
            continue
    raise ValueError(f"Invalid date value: {value}")


def normalized_record_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("project_name"),
        record.get("agency_name"),
        record.get("province"),
        record.get("procurement_method"),
        record.get("procurement_category"),
        record.get("budget_amount"),
        record.get("announcement_date"),
        record.get("raw_text"),
    ]
    return " | ".join(str(part) for part in parts if part not in (None, ""))


def content_hash(record: dict[str, Any]) -> str:
    identity = "|".join(
        str(record.get(key) or "").casefold()
        for key in (
            "dataset_type",
            "source_record_id",
            "project_name",
            "agency_name",
            "announcement_date",
            "budget_amount",
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
