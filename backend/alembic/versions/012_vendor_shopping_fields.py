"""Add shopping data fields to vendors table.

Revision ID: 012_vendor_shopping_fields
Revises: 011_deepresearch_fields

Adds:
- vendors: shopping_data, price_range_min, price_range_max, price_last_updated
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '012_vendor_shopping_fields'
down_revision = '011_deepresearch_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add shopping fields to vendors table
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shopping_data', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('price_range_min', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_range_max', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('price_last_updated', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove shopping fields from vendors table
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        batch_op.drop_column('price_last_updated')
        batch_op.drop_column('price_range_max')
        batch_op.drop_column('price_range_min')
        batch_op.drop_column('shopping_data')
