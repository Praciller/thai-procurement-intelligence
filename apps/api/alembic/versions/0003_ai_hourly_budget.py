"""Create a shared global hourly external inference budget.

Revision ID: 0003_ai_hourly_budget
Revises: 0002_official_provenance
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_ai_hourly_budget"
down_revision = "0002_official_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_hourly_budget",
        sa.Column("bucket", sa.String(length=80), nullable=False),
        sa.Column("window", sa.String(length=10), nullable=False),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("bucket", "window"),
    )


def downgrade() -> None:
    op.drop_table("ai_hourly_budget")
