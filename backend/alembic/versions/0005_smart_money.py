"""Smart money: COT instruments/reports + alert rules/events

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cot_instruments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cftc_code", sa.String(16), unique=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("exchange", sa.String(64), nullable=True),
        sa.Column("related_series_id", sa.String(32), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "cot_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("instrument_id", UUID(as_uuid=True), sa.ForeignKey("cot_instruments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("open_interest", sa.BigInteger(), nullable=True),
        sa.Column("noncomm_long", sa.BigInteger(), nullable=True),
        sa.Column("noncomm_short", sa.BigInteger(), nullable=True),
        sa.Column("noncomm_spread", sa.BigInteger(), nullable=True),
        sa.Column("comm_long", sa.BigInteger(), nullable=True),
        sa.Column("comm_short", sa.BigInteger(), nullable=True),
        sa.Column("net_noncomm", sa.BigInteger(), nullable=True),
        sa.Column("net_noncomm_pct_oi", sa.Float(), nullable=True),
        sa.Column("change_noncomm_long", sa.BigInteger(), nullable=True),
        sa.Column("change_noncomm_short", sa.BigInteger(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source_url", sa.String(512), nullable=False, server_default=""),
        sa.UniqueConstraint("instrument_id", "report_date", name="uq_cot_instrument_date"),
    )
    op.create_index("ix_cot_reports_instrument_date", "cot_reports", ["instrument_id", "report_date"])

    op.create_table(
        "alert_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("rule_type", sa.String(32), nullable=False),
        sa.Column("series_id", sa.String(32), nullable=True),
        sa.Column("cftc_code", sa.String(16), nullable=True),
        sa.Column("condition", sa.String(32), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_alert_rules_user", "alert_rules", ["user_id"])

    op.create_table(
        "alert_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_id", UUID(as_uuid=True), sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("value_at_trigger", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_events_user_triggered", "alert_events", ["user_id", "triggered_at"])


def downgrade() -> None:
    op.drop_index("ix_alert_events_user_triggered", table_name="alert_events")
    op.drop_table("alert_events")
    op.drop_index("ix_alert_rules_user", table_name="alert_rules")
    op.drop_table("alert_rules")
    op.drop_index("ix_cot_reports_instrument_date", table_name="cot_reports")
    op.drop_table("cot_reports")
    op.drop_table("cot_instruments")
