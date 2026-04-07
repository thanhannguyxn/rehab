"""empty message

Revision ID: 02f0c174ec7e
Revises: 87d26bafb5c0, add_emotion_tracking, d0a1b2c3d4e5
Create Date: 2026-04-07 02:02:54.624573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02f0c174ec7e'
down_revision: Union[str, Sequence[str], None] = ('87d26bafb5c0', 'add_emotion_tracking', 'd0a1b2c3d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Thêm cột cho bảng session_frames
    op.add_column('session_frames', sa.Column('emotion_state', sa.String(length=50), nullable=True))
    op.add_column('session_frames', sa.Column('emotion_confidence', sa.Float(), nullable=True))
    op.add_column('session_frames', sa.Column('pain_level', sa.Float(), nullable=True))
    op.add_column('session_frames', sa.Column('fatigue_level', sa.Float(), nullable=True))
    op.add_column('session_frames', sa.Column('emotion_metrics', sa.Text(), nullable=True))

    # Thêm cột cho bảng sessions
    op.add_column('sessions', sa.Column('avg_pain_level', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('avg_fatigue_level', sa.Float(), nullable=True))
    op.add_column('sessions', sa.Column('predominant_emotion', sa.String(length=50), nullable=True))
    op.add_column('sessions', sa.Column('pain_incidents', sa.Integer(), nullable=True))
    op.add_column('sessions', sa.Column('fatigue_incidents', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Xoá cột bảng sessions
    op.drop_column('sessions', 'fatigue_incidents')
    op.drop_column('sessions', 'pain_incidents')
    op.drop_column('sessions', 'predominant_emotion')
    op.drop_column('sessions', 'avg_fatigue_level')
    op.drop_column('sessions', 'avg_pain_level')

    # Xoá cột bảng session_frames
    op.drop_column('session_frames', 'emotion_metrics')
    op.drop_column('session_frames', 'fatigue_level')
    op.drop_column('session_frames', 'pain_level')
    op.drop_column('session_frames', 'emotion_confidence')
    op.drop_column('session_frames', 'emotion_state')
