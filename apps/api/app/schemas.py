from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ProcurementRecordBase(BaseModel):
    source_name: str
    dataset_type: Literal["synthetic", "official_snapshot"]
    source_record_id: str | None = None
    project_name: str
    agency_name: str | None = None
    province: str | None = None
    procurement_method: str | None = None
    procurement_category: str | None = None
    budget_amount: Decimal | None = None
    winning_amount: Decimal | None = None
    winner_name: str | None = None
    announcement_date: date | None = None
    contract_date: date | None = None
    source_url: str | None = None
    source_snapshot_id: str | None = None
    source_retrieved_at: datetime | None = None
    source_published_at: datetime | None = None
    source_updated_at: datetime | None = None
    source_license: str | None = None
    source_checksum: str | None = None
    mapping_version: str | None = None
    is_synthetic: bool
    raw_text: str | None = None
    normalized_text: str | None = None


class ProcurementRecordListItem(ProcurementRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_hash: str
    imported_at: datetime
    updated_at: datetime
    relevance_score: float | None = None


class ProcurementRecordDetail(ProcurementRecordListItem):
    created_at: datetime
    ai_summary: str | None = None


class RecordsResponse(BaseModel):
    items: list[ProcurementRecordListItem]
    total: int
    page: int
    page_size: int


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_name: str
    snapshot_id: str | None
    mapping_version: str | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    total_rows: int
    inserted_rows: int
    updated_rows: int
    skipped_rows: int
    failed_rows: int
    duplicate_rows: int
    warning_rows: int
    normalized_rows: int
    unchanged_rows: int
    error_message: str | None


class ImportResult(BaseModel):
    run_id: str
    total_rows: int
    inserted_rows: int
    updated_rows: int
    skipped_rows: int
    failed_rows: int
    status: str


class SummaryResponse(BaseModel):
    procurement_id: str
    provider: str
    model: str
    summary_text: str
    cached: bool


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(10, ge=1, le=50)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1)
    filters: dict[str, Any] | None = None
    limit: int = Field(8, ge=1, le=12)


class Citation(BaseModel):
    id: str
    project_name: str
    agency_name: str | None
    source_url: str | None = None
    source_record_id: str | None = None
    source_snapshot_id: str | None = None


class DatasetStatus(BaseModel):
    dataset_mode: Literal["synthetic", "official_snapshot"]
    freshness_status: Literal["not_applicable", "unknown", "current_snapshot", "stale_snapshot"]
    source: dict[str, Any] | None
    quality: dict[str, Any] | None
    latest_run: IngestionRunResponse | None


class AssistantResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_records: list[ProcurementRecordListItem]
    ai_enabled: bool


class AnalyticsBucket(BaseModel):
    label: str
    count: int
    total_budget: Decimal | None = None


class AnalyticsOverview(BaseModel):
    total_records: int
    total_budget: Decimal
    average_budget: Decimal
    records_by_province: list[AnalyticsBucket]
    records_by_category: list[AnalyticsBucket]
    records_by_month: list[AnalyticsBucket]
    top_agencies: list[AnalyticsBucket]
    top_projects: list[ProcurementRecordListItem]


SearchMode = Literal["keyword", "semantic", "hybrid"]
