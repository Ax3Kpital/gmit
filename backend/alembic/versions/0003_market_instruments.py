"""Add category and display_name to macro_series; seed market instruments

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("macro_series", sa.Column("category", sa.String(32), nullable=False, server_default="macro"))
    op.add_column("macro_series", sa.Column("display_name", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("macro_series", "display_name")
    op.drop_column("macro_series", "category")
