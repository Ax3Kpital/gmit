"""geopolitics — geo_events, geo_risk_index, geo_news_articles

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'geo_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('region_key', sa.String(64), nullable=False),
        sa.Column('region_label', sa.String(128), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('article_count', sa.Integer()),
        sa.Column('avg_tone', sa.Float()),   # GDELT tone: negative = conflict/bad
        sa.Column('top_themes', JSONB),      # list of theme strings
        sa.Column('query_used', sa.String(512)),
        sa.Column('data_status', sa.String(32), nullable=False, server_default='UNKNOWN'),
        sa.Column('retrieved_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_geo_events_region_date', 'geo_events', ['region_key', 'event_date'])

    op.create_table(
        'geo_risk_index',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('period', sa.Date(), nullable=False, unique=True),  # first of month
        sa.Column('gpr_value', sa.Float()),      # overall GPR index
        sa.Column('gpr_threat', sa.Float()),     # threat component (GPRT)
        sa.Column('gpr_act', sa.Float()),        # acts component (GPRA)
        sa.Column('data_status', sa.String(32), nullable=False, server_default='UNKNOWN'),
        sa.Column('retrieved_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_geo_risk_index_period', 'geo_risk_index', ['period'])

    op.create_table(
        'geo_news_articles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('region_key', sa.String(64), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text()),
        sa.Column('domain', sa.String(256)),
        sa.Column('source_country', sa.String(64)),
        sa.Column('language', sa.String(32)),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('retrieved_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_geo_news_region_pub', 'geo_news_articles',
                    ['region_key', 'published_at'])


def downgrade() -> None:
    op.drop_index('ix_geo_news_region_pub', 'geo_news_articles')
    op.drop_table('geo_news_articles')
    op.drop_index('ix_geo_risk_index_period', 'geo_risk_index')
    op.drop_table('geo_risk_index')
    op.drop_index('ix_geo_events_region_date', 'geo_events')
    op.drop_table('geo_events')
