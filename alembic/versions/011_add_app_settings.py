"""Add app_settings table

Revision ID: 011
Revises: 010
Create Date: 2026-02-24
"""
import sqlalchemy as sa
from alembic import op

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(100), primary_key=True, nullable=False),
        sa.Column('value', sa.String(500), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('app_settings')
