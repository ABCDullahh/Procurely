"""Add DeepResearch fields for iterative research and quality tracking.

Revision ID: 011_deepresearch_fields
Revises: 010_selected_providers

Adds:
- procurement_requests: locale, country_code, region_bias, research_config
- search_runs: research_iterations, research_queries, gap_analysis, quality_assessment, shopping_data
- vendor_metrics: quality_score, price_score, completeness_pct, confidence_pct, source_diversity, research_depth, price_competitiveness
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '011_deepresearch_fields'
down_revision = '010_selected_providers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fields to procurement_requests
    with op.batch_alter_table('procurement_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale', sa.String(10), nullable=False, server_default='id_ID'))
        batch_op.add_column(sa.Column('country_code', sa.String(2), nullable=False, server_default='ID'))
        batch_op.add_column(sa.Column('region_bias', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')))
        batch_op.add_column(sa.Column('research_config', sa.Text(), nullable=True))

    # Add fields to search_runs
    with op.batch_alter_table('search_runs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('research_iterations', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('research_queries', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('gap_analysis', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('quality_assessment', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('shopping_data', sa.Text(), nullable=True))

    # Add fields to vendor_metrics
    with op.batch_alter_table('vendor_metrics', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('price_score', sa.Float(), nullable=False, server_default='50.0'))
        batch_op.add_column(sa.Column('completeness_pct', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('confidence_pct', sa.Float(), nullable=False, server_default='0.0'))
        batch_op.add_column(sa.Column('source_diversity', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('research_depth', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('price_competitiveness', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove fields from vendor_metrics
    with op.batch_alter_table('vendor_metrics', schema=None) as batch_op:
        batch_op.drop_column('price_competitiveness')
        batch_op.drop_column('research_depth')
        batch_op.drop_column('source_diversity')
        batch_op.drop_column('confidence_pct')
        batch_op.drop_column('completeness_pct')
        batch_op.drop_column('price_score')
        batch_op.drop_column('quality_score')

    # Remove fields from search_runs
    with op.batch_alter_table('search_runs', schema=None) as batch_op:
        batch_op.drop_column('shopping_data')
        batch_op.drop_column('quality_assessment')
        batch_op.drop_column('gap_analysis')
        batch_op.drop_column('research_queries')
        batch_op.drop_column('research_iterations')

    # Remove fields from procurement_requests
    with op.batch_alter_table('procurement_requests', schema=None) as batch_op:
        batch_op.drop_column('research_config')
        batch_op.drop_column('region_bias')
        batch_op.drop_column('country_code')
        batch_op.drop_column('locale')
