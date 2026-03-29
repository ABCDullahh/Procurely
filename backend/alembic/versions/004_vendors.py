"""Add vendors and related tables.

Revision ID: 004_vendors
Revises: 003_procurement_requests
Create Date: 2025-12-28 11:20:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_vendors"
down_revision: Union[str, None] = "003_procurement_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vendors table
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=200), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("employee_count", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("pricing_model", sa.String(length=100), nullable=True),
        sa.Column("pricing_details", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendors_id"), "vendors", ["id"], unique=False)
    op.create_index(op.f("ix_vendors_name"), "vendors", ["name"], unique=False)

    # Create vendor_sources table
    op.create_table(
        "vendor_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("search_run_id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("page_title", sa.String(length=500), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("fetch_status", sa.String(length=20), nullable=False),
        sa.Column("fetch_error", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["search_run_id"], ["search_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_sources_id"), "vendor_sources", ["id"], unique=False)
    op.create_index(
        op.f("ix_vendor_sources_vendor_id"), "vendor_sources", ["vendor_id"], unique=False
    )
    op.create_index(
        op.f("ix_vendor_sources_search_run_id"),
        "vendor_sources",
        ["search_run_id"],
        unique=False,
    )

    # Create vendor_field_evidence table
    op.create_table(
        "vendor_field_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(length=1000), nullable=True),
        sa.Column("evidence_snippet", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, default=1.0),
        sa.Column("extraction_method", sa.String(length=50), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["vendor_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_vendor_field_evidence_id"), "vendor_field_evidence", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_vendor_field_evidence_vendor_id"),
        "vendor_field_evidence",
        ["vendor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_vendor_field_evidence_field_name"),
        "vendor_field_evidence",
        ["field_name"],
        unique=False,
    )

    # Create vendor_metrics table
    op.create_table(
        "vendor_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("search_run_id", sa.Integer(), nullable=False),
        sa.Column("fit_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("trust_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("overall_score", sa.Float(), nullable=False, default=0.0),
        sa.Column("must_have_matched", sa.Integer(), nullable=False, default=0),
        sa.Column("must_have_total", sa.Integer(), nullable=False, default=0),
        sa.Column("nice_to_have_matched", sa.Integer(), nullable=False, default=0),
        sa.Column("nice_to_have_total", sa.Integer(), nullable=False, default=0),
        sa.Column("source_count", sa.Integer(), nullable=False, default=0),
        sa.Column("evidence_count", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["search_run_id"], ["search_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id"),
    )
    op.create_index(op.f("ix_vendor_metrics_id"), "vendor_metrics", ["id"], unique=False)
    op.create_index(
        op.f("ix_vendor_metrics_vendor_id"), "vendor_metrics", ["vendor_id"], unique=True
    )
    op.create_index(
        op.f("ix_vendor_metrics_search_run_id"),
        "vendor_metrics",
        ["search_run_id"],
        unique=False,
    )

    # Create vendor_assets table
    op.create_table(
        "vendor_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("asset_url", sa.String(length=1000), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_assets_id"), "vendor_assets", ["id"], unique=False)
    op.create_index(
        op.f("ix_vendor_assets_vendor_id"), "vendor_assets", ["vendor_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vendor_assets_vendor_id"), table_name="vendor_assets")
    op.drop_index(op.f("ix_vendor_assets_id"), table_name="vendor_assets")
    op.drop_table("vendor_assets")

    op.drop_index(op.f("ix_vendor_metrics_search_run_id"), table_name="vendor_metrics")
    op.drop_index(op.f("ix_vendor_metrics_vendor_id"), table_name="vendor_metrics")
    op.drop_index(op.f("ix_vendor_metrics_id"), table_name="vendor_metrics")
    op.drop_table("vendor_metrics")

    op.drop_index(
        op.f("ix_vendor_field_evidence_field_name"), table_name="vendor_field_evidence"
    )
    op.drop_index(
        op.f("ix_vendor_field_evidence_vendor_id"), table_name="vendor_field_evidence"
    )
    op.drop_index(op.f("ix_vendor_field_evidence_id"), table_name="vendor_field_evidence")
    op.drop_table("vendor_field_evidence")

    op.drop_index(op.f("ix_vendor_sources_search_run_id"), table_name="vendor_sources")
    op.drop_index(op.f("ix_vendor_sources_vendor_id"), table_name="vendor_sources")
    op.drop_index(op.f("ix_vendor_sources_id"), table_name="vendor_sources")
    op.drop_table("vendor_sources")

    op.drop_index(op.f("ix_vendors_name"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_id"), table_name="vendors")
    op.drop_table("vendors")
