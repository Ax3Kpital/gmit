"""Research objects: theses, evidence, scenarios, counter-arguments

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "theses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("time_horizon", sa.String(8), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("catalysts", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("invalidation_conditions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("generation_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="completed"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_theses_user_created", "theses", ["user_id", "created_at"])

    op.create_table(
        "evidence_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("thesis_id", UUID(as_uuid=True), sa.ForeignKey("theses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("series_id", sa.String(32), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("obs_date", sa.Date(), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "scenarios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("thesis_id", UUID(as_uuid=True), sa.ForeignKey("theses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("probability", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trigger", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "counter_arguments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("thesis_id", UUID(as_uuid=True), sa.ForeignKey("theses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("argument", sa.Text(), nullable=False),
        sa.Column("strength", sa.String(16), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("counter_arguments")
    op.drop_table("scenarios")
    op.drop_table("evidence_items")
    op.drop_index("ix_theses_user_created", table_name="theses")
    op.drop_table("theses")
