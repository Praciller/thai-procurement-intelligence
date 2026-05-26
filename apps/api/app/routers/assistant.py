from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import AIQALog
from app.schemas import AssistantRequest, AssistantResponse, Citation, ProcurementRecordListItem
from app.services.embeddings import hash_embedding
from app.services.llm.factory import get_llm_provider
from app.services.rate_limit import check_hourly_ai_limit
from app.services.search import hybrid_candidates, keyword_candidates

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AssistantResponse)
async def ask(request: AssistantRequest, session: Session = Depends(get_session)) -> AssistantResponse:
    settings = get_settings()
    embedding = hash_embedding(request.question) if settings.enable_embeddings else None
    candidates = hybrid_candidates(session, request.question, embedding, limit=request.limit, filters=request.filters)
    if not candidates:
        candidates = keyword_candidates(session, request.question, limit=request.limit, filters=request.filters)
    records = [candidate.record for candidate in candidates]

    if settings.enable_llm or settings.llm_provider == "mock":
        provider = get_llm_provider(settings)
        if settings.enable_llm and not check_hourly_ai_limit(settings.ai_rate_limit_per_hour, bucket="assistant"):
            answer = "AI answering rate limit exceeded. Retrieved evidence records are shown below."
            ai_enabled = False
        else:
            answer = await provider.answer_question(request.question, records)
            ai_enabled = settings.enable_llm
    else:
        provider = get_llm_provider(settings)
        answer = "AI answering is disabled. Retrieved evidence records are shown below."
        ai_enabled = False

    session.add(
        AIQALog(
            question=request.question,
            answer=answer,
            retrieved_record_ids=[record.id for record in records],
            provider=provider.provider_name,
            model=provider.model_name,
        )
    )
    session.commit()

    return AssistantResponse(
        answer=answer,
        ai_enabled=ai_enabled,
        citations=[
            Citation(id=record.id, project_name=record.project_name, agency_name=record.agency_name, source_url=record.source_url)
            for record in records
        ],
        retrieved_records=[ProcurementRecordListItem.model_validate(record) for record in records],
    )
