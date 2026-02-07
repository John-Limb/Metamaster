"""Add batch operations table

Revision ID: 003
Revises: 002_add_database_indexes
Create Date: 2026-02-07 13:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002_add_database_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create batch_operations table"""
    op.create_table(
        "batch_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(50), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            index=True,
            server_default="pending",
        ),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "progress_percentage", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("eta", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_batch_operations_status", "batch_operations", ["status"])
    op.create_index("idx_batch_operations_type", "batch_operations", ["operation_type"])
    op.create_index("idx_batch_operations_created", "batch_operations", ["created_at"])


def downgrade() -> None:
    """Drop batch_operations table"""
    op.drop_index("idx_batch_operations_created", table_name="batch_operations")
    op.drop_index("idx_batch_operations_type", table_name="batch_operations")
    op.drop_index("idx_batch_operations_status", table_name="batch_operations")
    op.drop_table("batch_operations")
