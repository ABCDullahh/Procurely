"""add_ephemeral_and_source_to_procurement_request

Revision ID: 59a55c0d74f2
Revises: 012_vendor_shopping_fields
Create Date: 2026-01-11 15:47:46.172578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59a55c0d74f2'
down_revision: Union[str, None] = '012_vendor_shopping_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns with server_default for SQLite compatibility
    op.add_column('procurement_requests', sa.Column(
        'is_ephemeral', sa.Boolean(), nullable=False, server_default='0'
    ))
    op.add_column('procurement_requests', sa.Column(
        'source', sa.String(length=20), nullable=False, server_default='FORM'
    ))

    # Create index if it doesn't exist
    try:
        op.create_index(
            op.f('ix_vendor_field_evidence_source_id'),
            'vendor_field_evidence',
            ['source_id'],
            unique=False
        )
    except Exception:
        # Index may already exist
        pass


def downgrade() -> None:
    try:
        op.drop_index(op.f('ix_vendor_field_evidence_source_id'), table_name='vendor_field_evidence')
    except Exception:
        pass
    op.drop_column('procurement_requests', 'source')
    op.drop_column('procurement_requests', 'is_ephemeral')
