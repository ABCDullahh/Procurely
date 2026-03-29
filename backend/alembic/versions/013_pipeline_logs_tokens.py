"""Add pipeline logs and token usage to search_runs.

Revision ID: 013_pipeline_logs_tokens
Revises: 012_vendor_shopping_fields
Create Date: 2026-01-25
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "013_pipeline_logs_tokens"
down_revision = "59a55c0d74f2"  # After ephemeral/source migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add pipeline_logs and token_usage columns."""
    # Add pipeline_logs - JSON array of log entries
    op.add_column(
        "search_runs",
        sa.Column("pipeline_logs", sa.Text(), nullable=True),
    )

    # Add token_usage - JSON object with token counts per step
    op.add_column(
        "search_runs",
        sa.Column("token_usage", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove pipeline_logs and token_usage columns."""
    op.drop_column("search_runs", "token_usage")
    op.drop_column("search_runs", "pipeline_logs")
