"""005_shortlists

Revision ID: 005_shortlists
Revises: 004_vendors
Create Date: 2024-12-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_shortlists"
down_revision: Union[str, None] = "004_vendors"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create shortlists table
    op.create_table(
        "shortlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["procurement_requests.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_shortlists_id"), "shortlists", ["id"], unique=False)

    # Create shortlist_items table
    op.create_table(
        "shortlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shortlist_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["shortlist_id"],
            ["shortlists.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["vendors.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shortlist_id", "vendor_id", name="uq_shortlist_vendor"),
    )
    op.create_index(
        op.f("ix_shortlist_items_id"), "shortlist_items", ["id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_shortlist_items_id"), table_name="shortlist_items")
    op.drop_table("shortlist_items")
    op.drop_index(op.f("ix_shortlists_id"), table_name="shortlists")
    op.drop_table("shortlists")
