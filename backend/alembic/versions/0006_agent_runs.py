"""agent_runs and briefings

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_type', sa.String(64), nullable=False),
        sa.Column('trigger', sa.String(256)),
        sa.Column('status', sa.String(32), nullable=False, server_default='running'),
        sa.Column('input_data', JSONB),
        sa.Column('result_summary', sa.Text()),
        sa.Column('provider', sa.String(64)),
        sa.Column('model_name', sa.String(128)),
        sa.Column('input_tokens', sa.Integer()),
        sa.Column('output_tokens', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('started_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_ms', sa.Integer()),
    )
    op.create_index('ix_agent_runs_type_started', 'agent_runs',
                    ['agent_type', 'started_at'])

    op.create_table(
        'briefings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('date', sa.Date(), nullable=False, unique=True),
        sa.Column('macro_regime', sa.String(64)),
        sa.Column('headline', sa.Text()),
        sa.Column('sections', JSONB),
        sa.Column('raw_data', JSONB),
        sa.Column('agent_run_id', UUID(as_uuid=True),
                  sa.ForeignKey('agent_runs.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_briefings_date', 'briefings', ['date'])


def downgrade() -> None:
    op.drop_table('briefings')
    op.drop_index('ix_agent_runs_type_started', table_name='agent_runs')
    op.drop_table('agent_runs')
