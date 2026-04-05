"""add_chat_messages_table

Revision ID: d0a1b2c3d4e5
Revises: 18180c5375f6
Create Date: 2026-03-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = '18180c5375f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add chat_messages table for agent conversation history."""
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', name='conversationrole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_user_id', 'chat_messages', ['user_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index(
        'ix_chat_messages_user_agent_created',
        'chat_messages',
        ['user_id', 'agent_type', 'created_at']
    )


def downgrade() -> None:
    """Drop chat_messages table."""
    op.drop_index('ix_chat_messages_user_agent_created', 'chat_messages')
    op.drop_index('ix_chat_messages_created_at', 'chat_messages')
    op.drop_index('ix_chat_messages_user_id', 'chat_messages')
    op.drop_table('chat_messages')
