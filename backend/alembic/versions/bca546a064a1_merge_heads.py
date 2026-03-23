"""merge heads

Revision ID: bca546a064a1
Revises: 2dc5d45851f4, add_exercises_system
Create Date: 2026-03-22 15:05:25.855794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bca546a064a1'
down_revision: Union[str, Sequence[str], None] = ('2dc5d45851f4', 'add_exercises_system')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
