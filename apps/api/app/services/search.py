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
MIN_THAI_FUZZY_SCORE = 0.30
LOCAL_HASH_EMBEDDING_MODEL = "hashing-token-v1"
# Explicitly reviewed domain aliases; expand *only* the retrieval query,
# not stored evidence or the question passed to the answer generator.
RETRIEVAL_ALIASES = (("มอเตอร์ไซค์", "รถจักรยานยนต์"),)


def normalize_retrieval_terms(query: str) -> str:
    normalized = query.strip()
    for alias, canonical in RETRIEVAL_ALIASES:
        normalized = normalized.replace(alias, canonical)
    return normalized

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


def _contains_literal(column: Any, text: str) -> Any:
    """SQL LIKE escaping: search user-entered percent/underscore as literals."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


def apply_filters(stmt: Select, filters: dict[str, Any]) -> Select:
    clauses = [ProcurementRecord.dataset_type == get_settings().dataset_mode]
    if q := normalize_retrieval_terms(str(filters.get("q") or "")):
        text_fields = (
            ProcurementRecord.project_name,
            ProcurementRecord.agency_name,
            ProcurementRecord.raw_text,
            ProcurementRecord.normalized_text,
        )
        tokens = [token for token in tokenize(q) if len(token) >= 2]
        token_clauses = [_contains_literal(field, q) for field in text_fields]
        for token in tokens:
            token_clauses.extend(_contains_literal(field, token) for field in text_fields)
        clauses.append(or_(*token_clauses))
    if province := filters.get("province"):
        clauses.append(ProcurementRecord.province == province)
    if agency := filters.get("agency"):
        clauses.append(_contains_literal(ProcurementRecord.agency_name, agency))
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
    query = normalize_retrieval_terms(query)
    if not query:
        return []
    structured_filters = {key: value for key, value in (filters or {}).items() if key != "q"}
    stmt = apply_filters(select(ProcurementRecord), structured_filters).order_by(
        ProcurementRecord.source_name,
        ProcurementRecord.source_record_id,
        ProcurementRecord.content_hash,
        ProcurementRecord.id,
    )
    query_tokens = tokenize(query)
    query_has_thai = any(THAI_TOKEN_RE.fullmatch(token) for token in TOKEN_RE.findall(query))
    results = []
    for record in session.scalars(stmt).all():
        haystack = " ".join(
            value or ""
            for value in (record.project_name, record.agency_name, record.province, record.procurement_category, record.raw_text)
        )
        overlap = len(query_tokens & tokenize(haystack))
        phrase_match = query.strip().casefold() in haystack.casefold()
        score = 1.0 if phrase_match else overlap / max(len(query_tokens), 1)
        if score <= 0:
            continue
        if query_has_thai and not phrase_match and score < MIN_THAI_FUZZY_SCORE:
            continue
        results.append(SearchResult(record=record, score=score, exact_phrase=phrase_match))
    return sorted(results, key=lambda item: (-int(item.exact_phrase), -(item.score or 0), *_stable_record_key(item)))[:limit]


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
    query = query.strip()
    if not query:
        return []
    by_id: dict[str, SearchResult] = {}
    for rank, result in enumerate(keyword_candidates(session, query, limit=limit, filters=filters), start=1):
        by_id[result.record.id] = SearchResult(record=result.record, score=_rrf_score(rank, KEYWORD_WEIGHT))
    keyword_ids = set(by_id)
    if query_embedding:
        for rank, result in enumerate(semantic_candidates(session, query_embedding, limit=limit, filters=filters), start=1):
            # Hashing-token vectors are not semantic evidence: their collisions
            # must not introduce unrelated records absent from lexical search.
            # Real embedding models can still contribute semantic-only results.
            if result.record.id not in keyword_ids and all(
                embedded.embedding_model == LOCAL_HASH_EMBEDDING_MODEL
                for embedded in result.record.embeddings
            ):
                continue
            contribution = _rrf_score(rank, SEMANTIC_WEIGHT)
            existing = by_id.get(result.record.id)
            if existing:
                existing.score = (existing.score or 0) + contribution
            else:
                by_id[result.record.id] = SearchResult(record=result.record, score=contribution)
    return sorted(by_id.values(), key=lambda item: (-(item.score or 0), *_stable_record_key(item)))[:limit]


def grounded_local_semantic_candidates(
    session: Session,
    query: str,
    query_embedding: list[float],
    limit: int = 8,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    """Rerank lexical evidence with local hash vectors, never add hash-only hits.

    Deterministic hashing vectors are not true semantic embeddings and may
    collide on unrelated texts. Search results must have lexical support until
    a separately evaluated real semantic embedding pipeline exists.
    """
    lexical = keyword_candidates(session, query, limit=limit, filters=filters)
    if not lexical:
        return []

    ranked: list[SearchResult] = []
    for result in lexical:
        scores = [
            cosine_similarity(query_embedding, embedding.embedding)
            for embedding in result.record.embeddings
            if embedding.embedding_model == LOCAL_HASH_EMBEDDING_MODEL
            and embedding.embedding is not None
            and len(embedding.embedding) == len(query_embedding)
        ]
        ranked.append(
            SearchResult(
                record=result.record,
                score=max(scores) if scores else result.score,
                exact_phrase=result.exact_phrase,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (-int(item.exact_phrase), -(item.score or 0), *_stable_record_key(item)),
    )
