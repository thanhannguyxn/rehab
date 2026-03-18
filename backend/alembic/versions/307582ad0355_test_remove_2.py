"""test_remove_2

Revision ID: 307582ad0355
Revises: 48482f7922c7
Create Date: 2026-03-15 17:18:37.067923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '307582ad0355'
down_revision: Union[str, Sequence[str], None] = '48482f7922c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # No schema changes required (index/columns already handled by previous migrations).
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No schema changes to revert.
    pass
