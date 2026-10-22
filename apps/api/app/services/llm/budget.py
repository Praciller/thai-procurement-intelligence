"""Database-backed, atomic hourly quota for optional external model calls."""

from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AIHourlyBudget
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockLLMProvider


def consume_hourly_budget(session: Session, *, limit: int, now: datetime | None = None) -> bool:
    """Atomically reserve one global permit; never allow requests beyond limit."""
    if limit <= 0:
        return False
    window = (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%d%H")
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        insert = pg_insert
    elif dialect == "sqlite":
        insert = sqlite_insert
    else:
        raise RuntimeError("Unsupported database for shared AI quota")

    stmt = insert(AIHourlyBudget).values(bucket="external_llm", window=window, requests=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=[AIHourlyBudget.bucket, AIHourlyBudget.window],
        set_={"requests": AIHourlyBudget.requests + 1},
        where=AIHourlyBudget.requests < limit,
    )
    updated = session.execute(stmt).rowcount
    session.commit()
    return updated == 1


def protect_external_inference(session: Session, provider: LLMProvider, settings: Settings) -> LLMProvider:
    """Fall back to offline responses when the shared external budget is exhausted."""
    if not settings.enable_llm or not provider.may_call_external:
        return provider
    try:
        if consume_hourly_budget(session, limit=settings.ai_hourly_request_limit):
            return provider
    except (SQLAlchemyError, RuntimeError):
        session.rollback()
    return MockLLMProvider()
