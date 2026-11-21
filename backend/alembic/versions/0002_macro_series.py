"""Macro series and observations tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "macro_series",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("series_id", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.String(2048), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(512), nullable=False),
        sa.Column("units", sa.String(128), nullable=False),
        sa.Column("frequency", sa.String(64), nullable=False, server_default="Daily"),
        sa.Column("seasonal_adjustment", sa.String(64), nullable=True),
        sa.Column("data_status", sa.String(32), nullable=False, server_default="UNAVAILABLE"),
        sa.Column("stale_after_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("series_id", name="uq_macro_series_id"),
    )

    op.create_table(
        "macro_observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("macro_series_id", UUID(as_uuid=True), sa.ForeignKey("macro_series.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(512), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_status", sa.String(32), nullable=False),
        sa.Column("units", sa.String(128), nullable=False),
        sa.UniqueConstraint("macro_series_id", "date", name="uq_macro_obs_series_date"),
    )
    op.create_index("ix_macro_obs_series_date", "macro_observations", ["macro_series_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_macro_obs_series_date", table_name="macro_observations")
    op.drop_table("macro_observations")
    op.drop_table("macro_series")
