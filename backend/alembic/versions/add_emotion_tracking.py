"""Add emotion tracking to session frames

Revision ID: add_emotion_tracking
Revises: bca546a064a1
Create Date: 2026-03-22 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_emotion_tracking'
down_revision = 'bca546a064a1'  # Latest migration
branch_labels = None
depends_on = None

def upgrade():
    # Add emotion tracking columns to session_frames table
    with op.batch_alter_table('session_frames') as batch_op:
        batch_op.add_column(sa.Column('emotion_state', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('emotion_confidence', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('pain_level', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('fatigue_level', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('emotion_metrics', sa.Text, nullable=True))  # JSON string

    # Add emotion summary fields to sessions table
    with op.batch_alter_table('sessions') as batch_op:
        batch_op.add_column(sa.Column('avg_pain_level', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('avg_fatigue_level', sa.Float, nullable=True))
        batch_op.add_column(sa.Column('predominant_emotion', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('pain_incidents', sa.Integer, default=0))
        batch_op.add_column(sa.Column('fatigue_incidents', sa.Integer, default=0))

def downgrade():
    # Remove emotion columns from session_frames table
    with op.batch_alter_table('session_frames') as batch_op:
        batch_op.drop_column('emotion_state')
        batch_op.drop_column('emotion_confidence')
        batch_op.drop_column('pain_level')
        batch_op.drop_column('fatigue_level')
        batch_op.drop_column('emotion_metrics')

    # Remove emotion summary fields from sessions table
    with op.batch_alter_table('sessions') as batch_op:
        batch_op.drop_column('avg_pain_level')
        batch_op.drop_column('avg_fatigue_level')
        batch_op.drop_column('predominant_emotion')
        batch_op.drop_column('pain_incidents')
        batch_op.drop_column('fatigue_incidents')