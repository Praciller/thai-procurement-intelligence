from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import AISummary, ProcurementRecord
from app.schemas import ProcurementRecordDetail, RecordsResponse, SearchMode, SemanticSearchRequest, SummaryResponse
from app.services.embeddings import ensure_embedding, hash_embedding
from app.services.llm.factory import get_llm_provider
from app.services.rate_limit import check_hourly_ai_limit
from app.services.search import hybrid_candidates, keyword_candidates, search_records, semantic_candidates

router = APIRouter(prefix="/records", tags=["records"])
semantic_router = APIRouter(prefix="/search", tags=["search"])


def _detail_schema(record: ProcurementRecord) -> ProcurementRecordDetail:
    latest_summary = record.summaries[0].summary_text if record.summaries else None
    data = ProcurementRecordDetail.model_validate(record)
    data.ai_summary = latest_summary
    return data


@router.get("", response_model=RecordsResponse)
def list_records(
    q: str | None = None,
    province: str | None = None,
    agency: str | None = None,
    category: str | None = None,
    method: str | None = None,
    min_budget: float | None = None,
    max_budget: float | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search_mode: SearchMode = "keyword",
    session: Session = Depends(get_session),
) -> RecordsResponse:
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
        embedding = hash_embedding(q)
        if search_mode == "semantic":
            candidates = semantic_candidates(session, embedding, limit=page_size, filters={k: v for k, v in filters.items() if k != "q"})
        else:
            candidates = hybrid_candidates(session, q, embedding, limit=page_size, filters={k: v for k, v in filters.items() if k != "q"})
        items = []
        for candidate in candidates:
            item = ProcurementRecordDetail.model_validate(candidate.record)
            item.relevance_score = candidate.score
            items.append(item)
        return RecordsResponse(items=items, total=len(items), page=page, page_size=page_size)

    results, total = search_records(session, filters, page=page, page_size=page_size, sort=sort)
    items = []
    for result in results:
        item = ProcurementRecordDetail.model_validate(result.record)
        item.relevance_score = result.score
        items.append(item)
    return RecordsResponse(items=items, total=total, page=page, page_size=page_size)


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
async def summarize_record(record_id: str, session: Session = Depends(get_session)) -> SummaryResponse:
    settings = get_settings()
    record = session.get(ProcurementRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    provider = get_llm_provider(settings)
    cached = session.scalar(
        select(AISummary).where(
            AISummary.procurement_id == record.id,
            AISummary.provider == provider.provider_name,
            AISummary.model == provider.model_name,
        )
    )
    if cached:
        return SummaryResponse(
            procurement_id=record.id,
            provider=cached.provider,
            model=cached.model,
            summary_text=cached.summary_text,
            cached=True,
        )
    if not settings.enable_llm and settings.llm_provider != "mock":
        raise HTTPException(status_code=503, detail="LLM is disabled")
    if settings.enable_llm and not check_hourly_ai_limit(settings.ai_rate_limit_per_hour, bucket="summary"):
        raise HTTPException(status_code=429, detail="AI summary rate limit exceeded")
    summary_text = await provider.generate_summary(record)
    summary = AISummary(
        procurement_id=record.id,
        provider=provider.provider_name,
        model=provider.model_name,
        summary_text=summary_text,
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
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    embedding = ensure_embedding(session, record)
    return {"id": embedding.id, "model": embedding.embedding_model}
