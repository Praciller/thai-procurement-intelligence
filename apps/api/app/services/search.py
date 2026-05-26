from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import ProcurementEmbedding, ProcurementRecord


TOKEN_RE = re.compile(r"[\wก-๙]+", re.UNICODE)


@dataclass
class SearchResult:
    record: ProcurementRecord
    score: float | None = None


def tokenize(text: str) -> set[str]:
    return {token.casefold() for token in TOKEN_RE.findall(text or "")}


def apply_filters(stmt: Select, filters: dict[str, Any]) -> Select:
    clauses = []
    if q := filters.get("q"):
        text_fields = (
            ProcurementRecord.project_name,
            ProcurementRecord.agency_name,
            ProcurementRecord.raw_text,
            ProcurementRecord.normalized_text,
        )
        tokens = [token for token in tokenize(str(q)) if len(token) >= 2]
        phrase_like = f"%{q}%"
        token_clauses = [field.ilike(phrase_like) for field in text_fields]
        for token in tokens:
            like = f"%{token}%"
            token_clauses.extend(field.ilike(like) for field in text_fields)
        clauses.append(or_(*token_clauses))
    if province := filters.get("province"):
        clauses.append(ProcurementRecord.province == province)
    if agency := filters.get("agency"):
        clauses.append(ProcurementRecord.agency_name.ilike(f"%{agency}%"))
    if category := filters.get("category"):
        clauses.append(ProcurementRecord.procurement_category == category)
    if method := filters.get("method"):
        clauses.append(ProcurementRecord.procurement_method == method)
    if min_budget := filters.get("min_budget"):
        clauses.append(ProcurementRecord.budget_amount >= Decimal(str(min_budget)))
    if max_budget := filters.get("max_budget"):
        clauses.append(ProcurementRecord.budget_amount <= Decimal(str(max_budget)))
    if date_from := filters.get("date_from"):
        clauses.append(ProcurementRecord.announcement_date >= date_from)
    if date_to := filters.get("date_to"):
        clauses.append(ProcurementRecord.announcement_date <= date_to)
    if clauses:
        stmt = stmt.where(and_(*clauses))
    return stmt


def _sort(stmt: Select, sort: str | None) -> Select:
    match sort:
        case "budget_asc":
            return stmt.order_by(ProcurementRecord.budget_amount.asc().nullslast())
        case "budget_desc":
            return stmt.order_by(ProcurementRecord.budget_amount.desc().nullslast())
        case "date_asc":
            return stmt.order_by(ProcurementRecord.announcement_date.asc().nullslast())
        case _:
            return stmt.order_by(ProcurementRecord.announcement_date.desc().nullslast(), ProcurementRecord.created_at.desc())


def search_records(
    session: Session,
    filters: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
    sort: str | None = None,
) -> tuple[list[SearchResult], int]:
    base = apply_filters(select(ProcurementRecord), filters)
    total = session.scalar(select(func.count()).select_from(base.subquery())) or 0
    stmt = _sort(base, sort).offset((page - 1) * page_size).limit(page_size)
    return [SearchResult(record=row) for row in session.scalars(stmt).all()], total


def keyword_candidates(session: Session, query: str, limit: int = 8, filters: dict[str, Any] | None = None) -> list[SearchResult]:
    stmt = apply_filters(select(ProcurementRecord), {"q": query, **(filters or {})}).limit(limit * 3)
    query_tokens = tokenize(query)
    results = []
    for record in session.scalars(stmt).all():
        haystack = " ".join(
            value or ""
            for value in (record.project_name, record.agency_name, record.province, record.procurement_category, record.raw_text)
        )
        overlap = len(query_tokens & tokenize(haystack))
        results.append(SearchResult(record=record, score=float(overlap)))
    return sorted(results, key=lambda item: item.score or 0, reverse=True)[:limit]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


def semantic_candidates(
    session: Session,
    query_embedding: list[float],
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    stmt = apply_filters(select(ProcurementRecord).join(ProcurementEmbedding), filters or {})
    results = []
    for record in session.scalars(stmt).unique().all():
        if not record.embeddings:
            continue
        score = max(cosine_similarity(query_embedding, embedding.embedding or []) for embedding in record.embeddings)
        results.append(SearchResult(record=record, score=score))
    return sorted(results, key=lambda item: item.score or 0, reverse=True)[:limit]


def hybrid_candidates(
    session: Session,
    query: str,
    query_embedding: list[float] | None,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    by_id: dict[str, SearchResult] = {}
    for result in keyword_candidates(session, query, limit=limit, filters=filters):
        by_id[result.record.id] = SearchResult(record=result.record, score=(result.score or 0) * 0.55)
    if query_embedding:
        for result in semantic_candidates(session, query_embedding, limit=limit, filters=filters):
            existing = by_id.get(result.record.id)
            if existing:
                existing.score = (existing.score or 0) + (result.score or 0) * 0.45
            else:
                by_id[result.record.id] = SearchResult(record=result.record, score=(result.score or 0) * 0.45)
    return sorted(by_id.values(), key=lambda item: item.score or 0, reverse=True)[:limit]
