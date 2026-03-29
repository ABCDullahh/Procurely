"""Add vendor detail completeness fields.

Revision ID: 009
Revises: 008
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '009_vendor_detail_extensions'
down_revision = '008_app_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vendor table extensions
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('security_compliance', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('deployment', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('integrations', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('structured_data', sa.Text(), nullable=True))
    
    # VendorFieldEvidence table extensions
    with op.batch_alter_table('vendor_field_evidence', schema=None) as batch_op:
        batch_op.add_column(sa.Column('field_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('source_title', sa.String(500), nullable=True))
        batch_op.create_index('ix_vendor_field_evidence_category', ['category'])
    
    # VendorSource table extensions
    with op.batch_alter_table('vendor_sources', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_category', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('content_summary', sa.String(500), nullable=True))
        batch_op.create_index('ix_vendor_sources_source_category', ['source_category'])


def downgrade() -> None:
    # VendorSource rollback
    with op.batch_alter_table('vendor_sources', schema=None) as batch_op:
        batch_op.drop_index('ix_vendor_sources_source_category')
        batch_op.drop_column('content_summary')
        batch_op.drop_column('source_category')
    
    # VendorFieldEvidence rollback
    with op.batch_alter_table('vendor_field_evidence', schema=None) as batch_op:
        batch_op.drop_index('ix_vendor_field_evidence_category')
        batch_op.drop_column('source_title')
        batch_op.drop_column('category')
        batch_op.drop_column('field_label')
    
    # Vendor rollback
    with op.batch_alter_table('vendors', schema=None) as batch_op:
        batch_op.drop_column('structured_data')
        batch_op.drop_column('integrations')
        batch_op.drop_column('deployment')
        batch_op.drop_column('security_compliance')
