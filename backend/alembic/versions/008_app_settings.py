"""Add app_settings table for application configuration.

Revision ID: 008_app_settings
Revises: 007_api_keys_default_model
Create Date: 2025-12-30
"""
from alembic import op
import sqlalchemy as sa

revision = "008_app_settings"
down_revision = "007_api_keys_default_model"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    
    # Insert default search strategy setting
    op.execute(
        """
        INSERT INTO app_settings (key, value, description, updated_at)
        VALUES ('search_strategy', 'SERPER', 'Web search provider: SERPER or GEMINI_GROUNDING', now())
        """
    )


def downgrade():
    op.drop_table("app_settings")
