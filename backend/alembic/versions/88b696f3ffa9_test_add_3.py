"""test_add_3

Revision ID: 88b696f3ffa9
Revises: 307582ad0355
Create Date: 2026-03-15 17:27:38.045777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88b696f3ffa9'
down_revision: Union[str, Sequence[str], None] = '307582ad0355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove columns that are no longer used, only if they exist.
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='email'"
        )
    ).scalar()
    if exists:
        conn.execute(sa.text("ALTER TABLE users DROP COLUMN email"))

    exists = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='phone_number'"
        )
    ).scalar()
    if exists:
        conn.execute(sa.text("ALTER TABLE users DROP COLUMN phone_number"))


def downgrade() -> None:
    """Downgrade schema."""
    # Restore columns if rolling back.
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.create_unique_constraint(None, 'users', ['email'])
