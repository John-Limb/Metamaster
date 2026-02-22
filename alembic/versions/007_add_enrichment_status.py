"""Add enrichment_status and related columns to movies and tv_shows

Revision ID: 007
Revises: 006
Create Date: 2026-02-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

ENUM_NAME = 'enrichmentstatus'
ENUM_VALUES = ('pending_local', 'local_only', 'pending_external', 'fully_enriched', 'external_failed', 'not_found')


def upgrade() -> None:
    enrichment_status_enum = postgresql.ENUM(*ENUM_VALUES, name=ENUM_NAME)
    enrichment_status_enum.create(op.get_bind())

    for table in ('movies', 'tv_shows'):
        op.add_column(table, sa.Column('enrichment_status', sa.Enum(*ENUM_VALUES, name=ENUM_NAME), nullable=False, server_default='pending_local'))
        op.add_column(table, sa.Column('detected_external_id', sa.String(50), nullable=True))
        op.add_column(table, sa.Column('manual_external_id', sa.String(50), nullable=True))
        op.add_column(table, sa.Column('enrichment_error', sa.Text(), nullable=True))


def downgrade() -> None:
    for table in ('tv_shows', 'movies'):
        op.drop_column(table, 'enrichment_error')
        op.drop_column(table, 'manual_external_id')
        op.drop_column(table, 'detected_external_id')
        op.drop_column(table, 'enrichment_status')

    postgresql.ENUM(name=ENUM_NAME).drop(op.get_bind())
