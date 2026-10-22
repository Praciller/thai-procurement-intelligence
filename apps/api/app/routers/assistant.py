from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_session
from app.models import AIQALog
from app.schemas import AssistantRequest, AssistantResponse, Citation, ProcurementRecordListItem
from app.services.embeddings import hash_embedding
from app.services.llm.factory import get_llm_provider
from app.services.llm.limits import enforce_external_provider_limits
from app.services.llm.prompts import question_messages
from app.services.search import hybrid_candidates, keyword_candidates, normalize_assistant_query

router = APIRouter(prefix="/assistant", tags=["assistant"])
NO_EVIDENCE_ANSWER = "Cannot determine from available procurement records."


@router.post("/ask", response_model=AssistantResponse)
async def ask(body: AssistantRequest, request: Request, session: Session = Depends(get_session)) -> AssistantResponse:
    settings = get_settings()
    retrieval_query = normalize_assistant_query(body.question)
    embedding = hash_embedding(retrieval_query) if settings.enable_embeddings and retrieval_query else None
    filters = body.filters.model_dump(exclude_none=True) if body.filters else None
    candidates = hybrid_candidates(session, retrieval_query, embedding, limit=body.limit, filters=filters)
    if not candidates:
        candidates = keyword_candidates(session, retrieval_query, limit=body.limit, filters=filters)
    records = [candidate.record for candidate in candidates]

    if not records:
        return AssistantResponse(
            answer=NO_EVIDENCE_ANSWER,
            ai_enabled=False,
            citations=[],
            retrieved_records=[],
        )

    provider = get_llm_provider(settings)
    enforce_external_provider_limits(provider, request, question_messages(body.question, records))
    answer = await provider.answer_question(body.question, records)

    session.add(
        AIQALog(
            question=body.question,
            answer=answer,
            retrieved_record_ids=[record.id for record in records],
            provider=provider.provider_name,
            model=provider.model_name,
        )
    )
    session.commit()

    return AssistantResponse(
        answer=answer,
        ai_enabled=provider.is_external,
        citations=[
            Citation(
                id=record.id,
                project_name=record.project_name,
                agency_name=record.agency_name,
                source_url=record.source_url,
                source_record_id=record.source_record_id,
                source_snapshot_id=record.source_snapshot_id,
            )
            for record in records
        ],
        retrieved_records=[ProcurementRecordListItem.model_validate(record) for record in records],
    )
