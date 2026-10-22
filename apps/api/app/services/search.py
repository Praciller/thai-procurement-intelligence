from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from heapq import heappush, heapreplace
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
MIN_THAI_FUZZY_SCORE = 0.30
MAX_RANKED_SEARCH_RESULTS = 5_000
ASSISTANT_QUERY_STOP_PHRASES = (
    "จากข้อมูลที่ให้เท่านั้น",
    "จากข้อมูลที่ค้นพบ",
    "มีโครงการเกี่ยวกับ",
    "ตอบสั้น ๆ",
    "ตอบสั้นๆ",
    "อะไรบ้าง",
)


@dataclass
class SearchResult:
    record: ProcurementRecord
    score: float | None = None
    exact_phrase: bool = False


@dataclass
class _HeapCandidate:
    key: tuple[Any, ...]
    result: SearchResult

    def __lt__(self, other: _HeapCandidate) -> bool:
        return self.key > other.key


def _keep_top(heap: list[_HeapCandidate], result: SearchResult, key: tuple[Any, ...], limit: int) -> None:
    if limit <= 0:
        return
    candidate = _HeapCandidate(key, result)
    if len(heap) < limit:
        heappush(heap, candidate)
    elif key < heap[0].key:
        heapreplace(heap, candidate)


def _sorted_top(heap: list[_HeapCandidate]) -> list[SearchResult]:
    return [candidate.result for candidate in sorted(heap, key=lambda candidate: candidate.key)]


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


def normalize_assistant_query(question: str) -> str:
    """Remove deterministic Thai conversational wrappers before retrieval only."""
    normalized = " ".join((question or "").split())
    for phrase in ASSISTANT_QUERY_STOP_PHRASES:
        normalized = re.sub(re.escape(phrase), " ", normalized, flags=re.IGNORECASE)
    return " ".join(normalized.split())


def apply_filters(stmt: Select, filters: dict[str, Any]) -> Select:
    clauses = [ProcurementRecord.dataset_type == get_settings().dataset_mode]
    if q := str(filters.get("q") or "").strip():
        text_fields = (
            ProcurementRecord.project_name,
            ProcurementRecord.agency_name,
            ProcurementRecord.province,
            ProcurementRecord.procurement_category,
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


def keyword_candidates_with_total(
    session: Session,
    query: str,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> tuple[list[SearchResult], int, int]:
    query = query.strip()
    if not query:
        return [], 0, 0
    structured_filters = {key: value for key, value in (filters or {}).items() if key != "q"}
    structured_filters["q"] = query
    stable = (
        ProcurementRecord.source_name,
        ProcurementRecord.source_record_id,
        ProcurementRecord.content_hash,
        ProcurementRecord.id,
    )
    stmt = apply_filters(
        select(ProcurementRecord, ProcurementEmbedding.id).outerjoin(
            ProcurementEmbedding,
            ProcurementEmbedding.procurement_id == ProcurementRecord.id,
        ),
        structured_filters,
    ).order_by(*stable, ProcurementEmbedding.id)
    query_tokens = tokenize(query)
    query_has_thai = any(THAI_TOKEN_RE.fullmatch(token) for token in TOKEN_RE.findall(query))

    def score_record(record: ProcurementRecord, has_embedding: bool, heap: list[_HeapCandidate]) -> tuple[int, int]:
        haystack = " ".join(
            value or ""
            for value in (record.project_name, record.agency_name, record.province, record.procurement_category, record.raw_text)
        )
        overlap = len(query_tokens & tokenize(haystack))
        phrase_match = query.strip().casefold() in haystack.casefold()
        score = 1.0 if phrase_match else overlap / max(len(query_tokens), 1)
        if score <= 0:
            return 0, 0
        if query_has_thai and not phrase_match and score < MIN_THAI_FUZZY_SCORE:
            return 0, 0
        result = SearchResult(record=record, score=score, exact_phrase=phrase_match)
        _keep_top(heap, result, (-int(phrase_match), -score, *_stable_record_key(result)), limit)
        return 1, int(has_embedding)

    heap: list[_HeapCandidate] = []
    total = 0
    embedded_total = 0
    current_record: ProcurementRecord | None = None
    has_embedding = False
    for record, embedding_id in session.execute(stmt).yield_per(200):
        if current_record is not None and record.id != current_record.id:
            count, embedded_count = score_record(current_record, has_embedding, heap)
            total += count
            embedded_total += embedded_count
            has_embedding = False
        current_record = record
        has_embedding = has_embedding or embedding_id is not None
    if current_record is not None:
        count, embedded_count = score_record(current_record, has_embedding, heap)
        total += count
        embedded_total += embedded_count

    return _sorted_top(heap), total, embedded_total


def keyword_candidates(
    session: Session,
    query: str,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    results, _, _ = keyword_candidates_with_total(session, query, limit=limit, filters=filters)
    return results


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if not mag_a or not mag_b:
        return 0.0
    return dot / (mag_a * mag_b)


def semantic_candidates_with_total(
    session: Session,
    query_embedding: list[float],
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> tuple[list[SearchResult], int]:
    stmt = apply_filters(
        select(ProcurementRecord, ProcurementEmbedding.embedding)
        .join(ProcurementEmbedding, ProcurementEmbedding.procurement_id == ProcurementRecord.id),
        filters or {},
    ).order_by(ProcurementRecord.id, ProcurementEmbedding.id)
    heap: list[_HeapCandidate] = []
    total = 0
    current_record: ProcurementRecord | None = None
    current_score: float | None = None

    def score_record(record: ProcurementRecord, score: float) -> None:
        nonlocal total
        result = SearchResult(record=record, score=score)
        _keep_top(heap, result, (-score, *_stable_record_key(result)), limit)
        total += 1

    for record, vector in session.execute(stmt).yield_per(200):
        if current_record is not None and record.id != current_record.id:
            score_record(current_record, current_score if current_score is not None else 0.0)
            current_score = None
        current_record = record
        similarity = cosine_similarity(query_embedding, vector or [])
        current_score = similarity if current_score is None else max(current_score, similarity)
    if current_record is not None:
        score_record(current_record, current_score if current_score is not None else 0.0)

    return _sorted_top(heap), total


def semantic_candidates(
    session: Session,
    query_embedding: list[float],
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    results, _ = semantic_candidates_with_total(session, query_embedding, limit=limit, filters=filters)
    return results


def _rrf_score(rank: int, weight: float) -> float:
    return weight / (RRF_K + rank)


def hybrid_candidates(
    session: Session,
    query: str,
    query_embedding: list[float] | None,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    results, _ = hybrid_candidates_with_total(session, query, query_embedding, limit=limit, filters=filters)
    return results


def hybrid_candidates_with_total(
    session: Session,
    query: str,
    query_embedding: list[float] | None,
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> tuple[list[SearchResult], int]:
    query = query.strip()
    if not query:
        return [], 0
    by_id: dict[str, SearchResult] = {}
    keyword_results, keyword_total, keyword_embedding_overlap = keyword_candidates_with_total(session, query, limit=limit, filters=filters)
    for rank, result in enumerate(keyword_results, start=1):
        by_id[result.record.id] = SearchResult(record=result.record, score=_rrf_score(rank, KEYWORD_WEIGHT))
    semantic_total = 0
    if query_embedding:
        semantic_results, semantic_total = semantic_candidates_with_total(session, query_embedding, limit=limit, filters=filters)
        for rank, result in enumerate(semantic_results, start=1):
            contribution = _rrf_score(rank, SEMANTIC_WEIGHT)
            existing = by_id.get(result.record.id)
            if existing:
                existing.score = (existing.score or 0) + contribution
            else:
                by_id[result.record.id] = SearchResult(record=result.record, score=contribution)
    results = sorted(by_id.values(), key=lambda item: (-(item.score or 0), *_stable_record_key(item)))[:limit]
    return results, keyword_total + semantic_total - keyword_embedding_overlap
