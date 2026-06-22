from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def new_id() -> str:
    return str(uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


JsonType = JSON().with_variant(JSONB, "postgresql")


class ProcurementRecord(Base):
    __tablename__ = "procurement_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_name: Mapped[str] = mapped_column(String(120), default="sample", index=True)
    dataset_type: Mapped[str] = mapped_column(String(40), default="synthetic", index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    agency_name: Mapped[str | None] = mapped_column(Text)
    province: Mapped[str | None] = mapped_column(String(120), index=True)
    procurement_method: Mapped[str | None] = mapped_column(String(160), index=True)
    procurement_category: Mapped[str | None] = mapped_column(String(160), index=True)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), index=True)
    winning_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    winner_name: Mapped[str | None] = mapped_column(Text)
    announcement_date: Mapped[date | None] = mapped_column(Date, index=True)
    contract_date: Mapped[date | None] = mapped_column(Date)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(160), index=True)
    source_retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_license: Mapped[str | None] = mapped_column(String(160))
    source_checksum: Mapped[str | None] = mapped_column(String(64))
    mapping_version: Mapped[str | None] = mapped_column(String(80))
    is_synthetic: Mapped[bool] = mapped_column(default=True)
    raw_text: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    summaries: Mapped[list[AISummary]] = relationship(back_populates="record", cascade="all, delete-orphan")
    embeddings: Mapped[list[ProcurementEmbedding]] = relationship(back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_procurement_source_record", "source_name", "source_record_id"),
        Index("ix_procurement_date_budget", "announcement_date", "budget_amount"),
    )


class ProcurementEmbedding(Base):
    __tablename__ = "procurement_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    procurement_id: Mapped[str] = mapped_column(ForeignKey("procurement_records.id", ondelete="CASCADE"), index=True)
    embedding_model: Mapped[str] = mapped_column(String(160))
    embedding: Mapped[list[float] | None] = mapped_column(JsonType)
    embedded_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    record: Mapped[ProcurementRecord] = relationship(back_populates="embeddings")

    __table_args__ = (UniqueConstraint("procurement_id", "embedding_model", name="uq_embedding_record_model"),)


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    procurement_id: Mapped[str] = mapped_column(ForeignKey("procurement_records.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(160))
    summary_language: Mapped[str] = mapped_column(String(16), default="th")
    summary_text: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(40), default="summary-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    record: Mapped[ProcurementRecord] = relationship(back_populates="summaries")

    __table_args__ = (UniqueConstraint("procurement_id", "provider", "model", "prompt_version", name="uq_summary_cache"),)


class AIExtraction(Base):
    __tablename__ = "ai_extractions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    procurement_id: Mapped[str] = mapped_column(ForeignKey("procurement_records.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(160))
    extracted_json: Mapped[dict] = mapped_column(JsonType)
    confidence_notes: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(40), default="extraction-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    snapshot_id: Mapped[str | None] = mapped_column(String(160), index=True)
    mapping_version: Mapped[str | None] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    inserted_rows: Mapped[int] = mapped_column(Integer, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0)
    normalized_rows: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    errors: Mapped[list[IngestionError]] = relationship(back_populates="run", cascade="all, delete-orphan")


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True)
    row_number: Mapped[int | None] = mapped_column(Integer)
    raw_payload: Mapped[dict] = mapped_column(JsonType)
    error_message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    run: Mapped[IngestionRun] = relationship(back_populates="errors")


class AIQALog(Base):
    __tablename__ = "ai_qa_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    retrieved_record_ids: Mapped[list[str]] = mapped_column(JsonType)
    provider: Mapped[str] = mapped_column(String(80), default="mock")
    model: Mapped[str] = mapped_column(String(160), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
