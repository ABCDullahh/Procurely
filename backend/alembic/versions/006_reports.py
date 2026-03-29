"""Migration: Create reports table.

Revision ID: 006_reports
Revises: 005_shortlists
Create Date: 2025-12-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_reports"
down_revision: Union[str, None] = "005_shortlists"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reports table."""
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False, server_default="HTML"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="COMPLETED"),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["search_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_run_id"), "reports", ["run_id"], unique=False)
    op.create_index(
        op.f("ix_reports_created_by_user_id"),
        "reports",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reports_created_at"),
        "reports",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop reports table."""
    op.drop_index(op.f("ix_reports_created_at"), table_name="reports")
    op.drop_index(op.f("ix_reports_created_by_user_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_run_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")
