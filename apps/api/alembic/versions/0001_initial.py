"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procurement_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_record_id", sa.String(length=160), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("project_name", sa.Text(), nullable=False),
        sa.Column("agency_name", sa.Text(), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("procurement_method", sa.String(length=160), nullable=True),
        sa.Column("procurement_category", sa.String(length=160), nullable=True),
        sa.Column("budget_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("winning_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("winner_name", sa.Text(), nullable=True),
        sa.Column("announcement_date", sa.Date(), nullable=True),
        sa.Column("contract_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )
    op.create_index("ix_procurement_records_province", "procurement_records", ["province"])
    op.create_index("ix_procurement_records_budget_amount", "procurement_records", ["budget_amount"])
    op.create_index("ix_procurement_records_announcement_date", "procurement_records", ["announcement_date"])
    op.create_index("ix_procurement_source_record", "procurement_records", ["source_name", "source_record_id"])
    op.create_index("ix_procurement_date_budget", "procurement_records", ["announcement_date", "budget_amount"])

    op.create_table(
        "procurement_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("procurement_id", sa.String(length=36), nullable=False),
        sa.Column("embedding_model", sa.String(length=160), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("embedded_text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["procurement_id"], ["procurement_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("procurement_id", "embedding_model", name="uq_embedding_record_model"),
    )
    op.create_index("ix_procurement_embeddings_procurement_id", "procurement_embeddings", ["procurement_id"])

    op.create_table(
        "ai_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("procurement_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("summary_language", sa.String(length=16), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["procurement_id"], ["procurement_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("procurement_id", "provider", "model", "prompt_version", name="uq_summary_cache"),
    )
    op.create_index("ix_ai_summaries_procurement_id", "ai_summaries", ["procurement_id"])

    op.create_table(
        "ai_extractions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("procurement_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("extracted_json", sa.JSON(), nullable=False),
        sa.Column("confidence_notes", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["procurement_id"], ["procurement_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_extractions_procurement_id", "ai_extractions", ["procurement_id"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("inserted_rows", sa.Integer(), nullable=False),
        sa.Column("updated_rows", sa.Integer(), nullable=False),
        sa.Column("skipped_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_errors_ingestion_run_id", "ingestion_errors", ["ingestion_run_id"])

    op.create_table(
        "ai_qa_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("retrieved_record_ids", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ai_qa_logs")
    op.drop_table("ingestion_errors")
    op.drop_table("ingestion_runs")
    op.drop_table("ai_extractions")
    op.drop_table("ai_summaries")
    op.drop_table("procurement_embeddings")
    op.drop_table("procurement_records")

