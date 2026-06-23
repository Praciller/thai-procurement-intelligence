"""official snapshot provenance and ingestion evidence

Revision ID: 0002_official_provenance
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_official_provenance"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("procurement_records", sa.Column("dataset_type", sa.String(40), nullable=False, server_default="synthetic"))
    op.add_column("procurement_records", sa.Column("source_snapshot_id", sa.String(160)))
    op.add_column("procurement_records", sa.Column("source_retrieved_at", sa.DateTime(timezone=True)))
    op.add_column("procurement_records", sa.Column("source_published_at", sa.DateTime(timezone=True)))
    op.add_column("procurement_records", sa.Column("source_updated_at", sa.DateTime(timezone=True)))
    op.add_column("procurement_records", sa.Column("source_license", sa.String(160)))
    op.add_column("procurement_records", sa.Column("source_checksum", sa.String(64)))
    op.add_column("procurement_records", sa.Column("mapping_version", sa.String(80)))
    op.add_column("procurement_records", sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_procurement_records_dataset_type", "procurement_records", ["dataset_type"])
    op.create_index("ix_procurement_records_source_snapshot_id", "procurement_records", ["source_snapshot_id"])

    op.add_column("ingestion_runs", sa.Column("snapshot_id", sa.String(160)))
    op.add_column("ingestion_runs", sa.Column("mapping_version", sa.String(80)))
    for name in ("duplicate_rows", "warning_rows", "normalized_rows", "unchanged_rows"):
        op.add_column("ingestion_runs", sa.Column(name, sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_ingestion_runs_snapshot_id", "ingestion_runs", ["snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_snapshot_id", table_name="ingestion_runs")
    for name in ("unchanged_rows", "normalized_rows", "warning_rows", "duplicate_rows", "mapping_version", "snapshot_id"):
        op.drop_column("ingestion_runs", name)
    op.drop_index("ix_procurement_records_source_snapshot_id", table_name="procurement_records")
    op.drop_index("ix_procurement_records_dataset_type", table_name="procurement_records")
    for name in (
        "is_synthetic",
        "mapping_version",
        "source_checksum",
        "source_license",
        "source_updated_at",
        "source_published_at",
        "source_retrieved_at",
        "source_snapshot_id",
        "dataset_type",
    ):
        op.drop_column("procurement_records", name)
