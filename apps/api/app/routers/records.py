from secrets import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import AISummary, ProcurementRecord
from app.schemas import ProcurementRecordDetail, RecordFacets, RecordsResponse, SearchMode, SemanticSearchRequest, SummaryResponse
from app.services.embeddings import ensure_embedding, hash_embedding
from app.services.llm.factory import get_llm_provider
from app.services.llm.limits import enforce_external_prompt_limit
from app.services.llm.prompts import summary_cache_version, summary_messages
from app.services.llm.budget import protect_external_inference
from app.services.search import grounded_local_semantic_candidates, hybrid_candidates, keyword_candidates, normalize_retrieval_terms, search_records

router = APIRouter(prefix="/records", tags=["records"])
semantic_router = APIRouter(prefix="/search", tags=["search"])
def _summary_version(record: ProcurementRecord) -> str:
    return summary_cache_version(record)



def _detail_schema(record: ProcurementRecord) -> ProcurementRecordDetail:
    current = (summary for summary in record.summaries if summary.prompt_version == _summary_version(record))
    latest = max(current, key=lambda summary: summary.created_at, default=None)
    latest_summary = latest.summary_text if latest else None
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
    q = q.strip() if q is not None else None
    if q and len(q) > 1000:
        raise HTTPException(status_code=422, detail="Search query exceeds 1000 characters")
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
        if page != 1:
            raise HTTPException(
                status_code=422,
                detail="Ranked search pagination is not supported; use page=1",
            )
        embedding = hash_embedding(normalize_retrieval_terms(q) if search_mode == "semantic" else q)
        if search_mode == "semantic":
            candidates = grounded_local_semantic_candidates(
                session, q, embedding, limit=page_size,
                filters={k: v for k, v in filters.items() if k != "q"},
            )
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


@router.get("/facets", response_model=RecordFacets)
def record_facets(session: Session = Depends(get_session)) -> RecordFacets:
    """Dataset-wide, not first-page-only filter options."""
    mode = get_settings().dataset_mode

    def values(column) -> list[str]:
        return list(
            session.scalars(
                select(column)
                .where(ProcurementRecord.dataset_type == mode, column.is_not(None), column != "")
                .distinct()
                .order_by(column)
            ).all()
        )

    return RecordFacets(
        provinces=values(ProcurementRecord.province),
        categories=values(ProcurementRecord.procurement_category),
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
async def summarize_record(record_id: str, session: Session = Depends(get_session)) -> SummaryResponse:
    settings = get_settings()
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != settings.dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    provider = get_llm_provider(settings)
    prompt_version = _summary_version(record)
    cached = session.scalar(
        select(AISummary).where(
            AISummary.procurement_id == record.id,
            AISummary.provider == provider.provider_name,
            AISummary.model == provider.model_name,
            AISummary.prompt_version == prompt_version,
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
    enforce_external_prompt_limit(provider, settings, summary_messages(record))
    provider = protect_external_inference(session, provider, settings)
    # On budget exhaustion, prefer a cached deterministic fallback if available.
    if provider.provider_name == "mock":
        fallback_cache = session.scalar(
            select(AISummary).where(
                AISummary.procurement_id == record.id,
                AISummary.provider == provider.provider_name,
                AISummary.model == provider.model_name,
                AISummary.prompt_version == prompt_version,
            )
        )
        if fallback_cache:
            return SummaryResponse(
                procurement_id=record.id,
                provider=fallback_cache.provider,
                model=fallback_cache.model,
                summary_text=fallback_cache.summary_text,
                cached=True,
            )
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
    embedding = hash_embedding(normalize_retrieval_terms(request.query))
    candidates = grounded_local_semantic_candidates(session, request.query, embedding, limit=request.limit)
    items = []
    for candidate in candidates:
        item = _detail_schema(candidate.record)
        item.relevance_score = candidate.score
        items.append(item)
    return items


@router.post("/{record_id}/embedding")
def generate_record_embedding(
    record_id: str,
    session: Session = Depends(get_session),
    x_admin_token: str | None = Header(None),
) -> dict[str, str]:
    settings = get_settings()
    record = session.get(ProcurementRecord, record_id)
    if not record or record.dataset_type != settings.dataset_mode:
        raise HTTPException(status_code=404, detail="Record not found")
    # Unlike read-only retrieval, generating embeddings writes persistent data.
    # Reuse the opt-in ingestion admin token and disable this endpoint by
    # default. Browser-facing read/assistant/summary routes remain unchanged.
    expected = settings.admin_ingestion_token
    if not expected or not x_admin_token or not compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="embedding generation is disabled")
    embedding = ensure_embedding(session, record)
    return {"id": embedding.id, "model": embedding.embedding_model}
