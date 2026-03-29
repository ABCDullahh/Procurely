"""Add procurement_requests and search_runs tables.

Revision ID: 003_procurement_requests
Revises: 002_api_keys_audit_logs
Create Date: 2024-12-28 10:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_procurement_requests"
down_revision: Union[str, None] = "002_api_keys_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create procurement_requests table
    op.create_table(
        "procurement_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("budget_min", sa.Integer(), nullable=True),
        sa.Column("budget_max", sa.Integer(), nullable=True),
        sa.Column("timeline", sa.String(length=100), nullable=True),
        sa.Column("must_have_criteria", sa.Text(), nullable=True),
        sa.Column("nice_to_have_criteria", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_procurement_requests_id"), "procurement_requests", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_procurement_requests_status"), "procurement_requests", ["status"], unique=False
    )

    # Create search_runs table
    op.create_table(
        "search_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_step", sa.String(length=50), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, default=0),
        sa.Column("vendors_found", sa.Integer(), nullable=False, default=0),
        sa.Column("sources_searched", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_runs_id"), "search_runs", ["id"], unique=False)
    op.create_index(op.f("ix_search_runs_status"), "search_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_search_runs_status"), table_name="search_runs")
    op.drop_index(op.f("ix_search_runs_id"), table_name="search_runs")
    op.drop_table("search_runs")
    op.drop_index(op.f("ix_procurement_requests_status"), table_name="procurement_requests")
    op.drop_index(op.f("ix_procurement_requests_id"), table_name="procurement_requests")
    op.drop_table("procurement_requests")
