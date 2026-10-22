from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import AISummary, ProcurementRecord
from app.schemas import ProcurementRecordDetail, RecordFacets, RecordsResponse, SearchMode, SemanticSearchRequest, SummaryResponse
from app.services.embeddings import ensure_embedding, hash_embedding
from app.services.llm.factory import get_llm_provider
from app.services.llm.limits import enforce_external_provider_limits
from app.services.llm.prompts import summary_cache_version, summary_messages
from app.services.search import (
    MAX_RANKED_SEARCH_RESULTS,
    hybrid_candidates_with_total,
    keyword_candidates,
    search_records,
    semantic_candidates,
    semantic_candidates_with_total,
)

router = APIRouter(prefix="/records", tags=["records"])
semantic_router = APIRouter(prefix="/search", tags=["search"])


def _detail_schema(record: ProcurementRecord) -> ProcurementRecordDetail:
    latest_summary = record.summaries[0].summary_text if record.summaries else None
    data = ProcurementRecordDetail.model_validate(record)
    data.ai_summary = latest_summary
    return data


@router.get("", response_model=RecordsResponse)
def list_records(
    q: str | None = Query(None, max_length=200),
    province: str | None = Query(None, max_length=120),
    agency: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=160),
    method: str | None = Query(None, max_length=160),
    min_budget: float | None = Query(None, ge=0, le=1_000_000_000_000_000),
    max_budget: float | None = Query(None, ge=0, le=1_000_000_000_000_000),
    date_from: str | None = Query(None, max_length=10),
    date_to: str | None = Query(None, max_length=10),
    sort: Literal["date_desc", "date_asc", "budget_desc", "budget_asc"] | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search_mode: SearchMode = "keyword",
    session: Session = Depends(get_session),
) -> RecordsResponse:
    q = q.strip() if q is not None else None
    filters = {
        "q": q,
        "province": province,
        "agency": agency,
        "category": category,
        "method": method,
        "min_budget": min_budget,
        "max_budget": max_budget,
        "date_from": date_from,
        "date_to": date_to,
    }
    filters = {key: value for key, value in filters.items() if value not in (None, "")}
    if search_mode in {"semantic", "hybrid"} and q:
        if sort is not None:
            raise HTTPException(status_code=422, detail="Sort is not supported with semantic or hybrid ranking")
        candidate_limit = page * page_size
        if candidate_limit > MAX_RANKED_SEARCH_RESULTS:
            raise HTTPException(status_code=422, detail=f"Ranked search is limited to the first {MAX_RANKED_SEARCH_RESULTS} results")
        embedding = hash_embedding(q)
        if search_mode == "semantic":
            candidates, total = semantic_candidates_with_total(
                session,
                embedding,
                limit=candidate_limit,
                filters={k: v for k, v in filters.items() if k != "q"},
            )
        else:
            candidates, total = hybrid_candidates_with_total(
                session,
                q,
                embedding,
                limit=candidate_limit,
                filters={k: v for k, v in filters.items() if k != "q"},
            )
        items = []
        start = (page - 1) * page_size
        for candidate in candidates[start : start + page_size]:
            item = ProcurementRecordDetail.model_validate(candidate.record)
            item.relevance_score = candidate.score
            items.append(item)
        return RecordsResponse(items=items, total=total, page=page, page_size=page_size)

    results, total = search_records(session, filters, page=page, page_size=page_size, sort=sort)
    items = []
    for result in results:
        item = ProcurementRecordDetail.model_validate(result.record)
        item.relevance_score = result.score
        items.append(item)
    return RecordsResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/facets", response_model=RecordFacets)
def record_facets(session: Session = Depends(get_session)) -> RecordFacets:
    dataset_type = get_settings().dataset_mode

    def values_for(column) -> list[str]:
        value = func.trim(column)
        values = session.scalars(
            select(value)
            .where(ProcurementRecord.dataset_type == dataset_type, column.is_not(None), value != "")
            .distinct()
        ).all()
        return sorted(values, key=lambda item: (item.casefold(), item))

    return RecordFacets(
        provinces=values_for(ProcurementRecord.province),
        categories=values_for(ProcurementRecord.procurement_category),
    )


@router.get("/{record_id}", response_model=ProcurementRecordDetail)
def get_record(record_id: str, session: Session = Depends(get_session)) -> ProcurementRecordDetail:
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != get_settings().dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    return _detail_schema(record)


@router.get("/{record_id}/similar", response_model=list[ProcurementRecordDetail])
def similar_records(record_id: str, session: Session = Depends(get_session)) -> list[ProcurementRecordDetail]:
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != get_settings().dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    query = " ".join(part or "" for part in (record.project_name, record.procurement_category, record.province))
    candidates = keyword_candidates(session, query, limit=6)
    return [_detail_schema(candidate.record) for candidate in candidates if candidate.record.id != record_id][:5]


@router.post("/{record_id}/summary", response_model=SummaryResponse)
async def summarize_record(record_id: str, request: Request, session: Session = Depends(get_session)) -> SummaryResponse:
    settings = get_settings()
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != settings.dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    provider = get_llm_provider(settings)
    prompt_version = summary_cache_version(record, provider.cache_identity)
    cached = session.scalar(
        select(AISummary)
        .where(
            AISummary.procurement_id == record.id,
            AISummary.provider.in_(provider.cache_provider_names),
            AISummary.prompt_version == prompt_version,
        )
        .order_by(AISummary.created_at.desc())
        .limit(1)
    )
    if cached:
        return SummaryResponse(
            procurement_id=record.id,
            provider=cached.provider,
            model=cached.model,
            summary_text=cached.summary_text,
            cached=True,
        )
    enforce_external_provider_limits(provider, request, summary_messages(record))
    summary_text = await provider.generate_summary(record)
    summary = AISummary(
        procurement_id=record.id,
        provider=provider.provider_name,
        model=provider.model_name,
        summary_text=summary_text,
        prompt_version=prompt_version,
    )
    session.add(summary)
    session.commit()
    return SummaryResponse(
        procurement_id=record.id,
        provider=provider.provider_name,
        model=provider.model_name,
        summary_text=summary_text,
        cached=False,
    )


@semantic_router.post("/semantic", response_model=list[ProcurementRecordDetail])
def semantic_search(request: SemanticSearchRequest, session: Session = Depends(get_session)) -> list[ProcurementRecordDetail]:
    embedding = hash_embedding(request.query)
    candidates = semantic_candidates(session, embedding, limit=request.limit)
    if not candidates:
        candidates = keyword_candidates(session, request.query, limit=request.limit)
    items = []
    for candidate in candidates:
        item = _detail_schema(candidate.record)
        item.relevance_score = candidate.score
        items.append(item)
    return items


@router.post("/{record_id}/embedding")
def generate_record_embedding(record_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != get_settings().dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    embedding = ensure_embedding(session, record)
    return {"id": embedding.id, "model": embedding.embedding_model}
