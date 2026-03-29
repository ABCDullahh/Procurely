"""Add selected_providers column to procurement_requests.

Revision ID: 010_selected_providers
Revises: 009_vendor_detail_extensions
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '010_selected_providers'
down_revision = '009_vendor_detail_extensions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('procurement_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('selected_providers', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('procurement_requests', schema=None) as batch_op:
        batch_op.drop_column('selected_providers')
