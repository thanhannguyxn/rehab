"""remove email and phone columns

Revision ID: b86f6a7b019d
Revises: 9bb8137a6269
Create Date: 2026-03-15 15:08:36.395217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b86f6a7b019d'
down_revision: Union[str, Sequence[str], None] = 'fa05a2078723'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the email and phone_number columns
    try:
        op.drop_column('users', 'email')
    except Exception:
        pass
    try:
        op.drop_column('users', 'phone_number')
    except Exception:
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the email and phone_number columns
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    # Note: We can't restore the unique constraint on email in downgrade
    # as it would require checking existing data
