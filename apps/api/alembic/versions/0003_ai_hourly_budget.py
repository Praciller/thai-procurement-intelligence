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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # An older app startup/import path used Base.metadata.create_all(). With a
    # newer ORM on revision 0002, it could accidentally precreate this table.
    # Accept only the exact intended schema; never silently stamp a malformed
    # or unrelated table as a successful migration.
    if inspector.has_table("ai_hourly_budget"):
        columns = {column["name"]: column for column in inspector.get_columns("ai_hourly_budget")}
        primary_key = inspector.get_pk_constraint("ai_hourly_budget").get("constrained_columns") or []
        expected = {"bucket", "window", "requests"}
        schema_valid = (
            set(columns) == expected
            and primary_key == ["bucket", "window"]
            and isinstance(columns["bucket"]["type"], sa.String)
            and columns["bucket"]["type"].length == 80
            and isinstance(columns["window"]["type"], sa.String)
            and columns["window"]["type"].length == 10
            and isinstance(columns["requests"]["type"], sa.Integer)
            and all(not column["nullable"] for column in columns.values())
        )
        if not schema_valid:
            raise RuntimeError(
                "Existing ai_hourly_budget schema differs from revision 0003; "
                "manual investigation required before migration."
            )
        return

    op.create_table(
        "ai_hourly_budget",
        sa.Column("bucket", sa.String(length=80), nullable=False),
        sa.Column("window", sa.String(length=10), nullable=False),
        sa.Column("requests", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("bucket", "window"),
    )


def downgrade() -> None:
    op.drop_table("ai_hourly_budget")
