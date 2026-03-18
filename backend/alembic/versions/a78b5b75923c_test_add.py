"""test_add

Revision ID: a78b5b75923c
Revises: b86f6a7b019d
Create Date: 2026-03-15 15:13:26.471218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a78b5b75923c'
down_revision: Union[str, Sequence[str], None] = 'b86f6a7b019d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Downgrade schema."""
    # Add back the email and phone_number columns
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))


def downgrade()  -> None:
    """Upgrade schema."""
    # Drop the email and phone_number columns
    op.drop_column('users', 'email')
    op.drop_column('users', 'phone_number')


