"""Add TaskError model for task error tracking

Revision ID: 001
Revises:
Create Date: 2026-02-07 10:19:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_add_task_error_model"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create task_errors table
    op.create_table(
        "task_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("error_traceback", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_task_errors_task_id", "task_errors", ["task_id"])
    op.create_index("idx_task_errors_created", "task_errors", ["created_at"])
    op.create_index("idx_task_errors_severity", "task_errors", ["severity"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_task_errors_severity", table_name="task_errors")
    op.drop_index("idx_task_errors_created", table_name="task_errors")
    op.drop_index("idx_task_errors_task_id", table_name="task_errors")

    # Drop table
    op.drop_table("task_errors")
