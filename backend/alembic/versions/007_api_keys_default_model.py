"""Add default_model column to api_keys.

Revision ID: 007_api_keys_default_model
Revises: 006_reports
Create Date: 2025-12-29
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007_api_keys_default_model"
down_revision: Union[str, None] = "006_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default_model column to api_keys table."""
    op.add_column(
        "api_keys",
        sa.Column("default_model", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    """Remove default_model column from api_keys table."""
    op.drop_column("api_keys", "default_model")
