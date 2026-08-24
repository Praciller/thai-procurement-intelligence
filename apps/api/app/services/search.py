from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import ProcurementEmbedding, ProcurementRecord


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u0E00-\u0E7F]+", re.UNICODE)
THAI_TOKEN_RE = re.compile(r"^[\u0E00-\u0E7F]+$")
RRF_K = 60
KEYWORD_WEIGHT = 0.55
SEMANTIC_WEIGHT = 0.45


@dataclass
class SearchResult:
    record: ProcurementRecord
    score: float | None = None


def _stable_record_key(result: SearchResult) -> tuple[str, str, str, str]:
    record = result.record
    return (record.source_name, record.source_record_id or "", record.content_hash, record.id)


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in TOKEN_RE.findall(text or ""):
        token = raw_token.casefold()
        tokens.add(token)
        if THAI_TOKEN_RE.fullmatch(token) and len(token) > 3:
            tokens.update(token[index : index + 3] for index in range(len(token) - 2))
    return tokens


def apply_filters(stmt: Select, filters: dict[str, Any]) -> Select:
    clauses = [ProcurementRecord.dataset_type == get_settings().dataset_mode]
    if q := str(filters.get("q") or "").strip():
        text_fields = (
            ProcurementRecord.project_name,
            ProcurementRecord.agency_name,
            ProcurementRecord.raw_text,
            ProcurementRecord.normalized_text,
        )
        tokens = [token for token in tokenize(q) if len(token) >= 2]
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
    if filters.get("min_budget") is not None:
        clauses.append(ProcurementRecord.budget_amount >= Decimal(str(filters["min_budget"])))
    if filters.get("max_budget") is not None:
        clauses.append(ProcurementRecord.budget_amount <= Decimal(str(filters["max_budget"])))
    if date_from := filters.get("date_from"):
        clauses.append(ProcurementRecord.announcement_date >= date_from)
    if date_to := filters.get("date_to"):
        clauses.append(ProcurementRecord.announcement_date <= date_to)
    if clauses:
        stmt = stmt.where(and_(*clauses))
    return stmt


def _sort(stmt: Select, sort: str | None) -> Select:
    stable = (
        ProcurementRecord.source_name,
        ProcurementRecord.source_record_id,
        ProcurementRecord.content_hash,
        ProcurementRecord.id,
    )
    match sort:
        case "budget_asc":
            return stmt.order_by(ProcurementRecord.budget_amount.asc().nullslast(), *stable)
        case "budget_desc":
            return stmt.order_by(ProcurementRecord.budget_amount.desc().nullslast(), *stable)
        case "date_asc":
            return stmt.order_by(ProcurementRecord.announcement_date.asc().nullslast(), *stable)
        case _:
            return stmt.order_by(ProcurementRecord.announcement_date.desc().nullslast(), *stable)


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


def keyword_candidates(
    session: Session,
    query: str,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    stmt = (
        apply_filters(select(ProcurementRecord), {"q": query, **(filters or {})})
        .order_by(
            ProcurementRecord.source_name,
            ProcurementRecord.source_record_id,
            ProcurementRecord.content_hash,
            ProcurementRecord.id,
        )
        .limit(limit * 3)
    )
    query_tokens = tokenize(query)
    results = []
    for record in session.scalars(stmt).all():
        haystack = " ".join(
            value or ""
            for value in (record.project_name, record.agency_name, record.province, record.procurement_category, record.raw_text)
        )
        overlap = len(query_tokens & tokenize(haystack))
        phrase_match = query.strip().casefold() in haystack.casefold()
        score = 1.0 if phrase_match else overlap / max(len(query_tokens), 1)
        results.append(SearchResult(record=record, score=score))
    return sorted(results, key=lambda item: (-(item.score or 0), *_stable_record_key(item)))[:limit]


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
    return sorted(results, key=lambda item: (-(item.score or 0), *_stable_record_key(item)))[:limit]


def _rrf_score(rank: int, weight: float) -> float:
    return weight / (RRF_K + rank)


def hybrid_candidates(
    session: Session,
    query: str,
    query_embedding: list[float] | None,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    by_id: dict[str, SearchResult] = {}
    for rank, result in enumerate(keyword_candidates(session, query, limit=limit, filters=filters), start=1):
        by_id[result.record.id] = SearchResult(record=result.record, score=_rrf_score(rank, KEYWORD_WEIGHT))
    if query_embedding:
        for rank, result in enumerate(semantic_candidates(session, query_embedding, limit=limit, filters=filters), start=1):
            contribution = _rrf_score(rank, SEMANTIC_WEIGHT)
            existing = by_id.get(result.record.id)
            if existing:
                existing.score = (existing.score or 0) + contribution
            else:
                by_id[result.record.id] = SearchResult(record=result.record, score=contribution)
    return sorted(by_id.values(), key=lambda item: (-(item.score or 0), *_stable_record_key(item)))[:limit]
