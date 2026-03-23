"""Add exercises system

Revision ID: add_exercises_system
Revises: 48482f7922c7
Create Date: 2025-03-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_exercises_system'
down_revision = '48482f7922c7'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create exercises table
    op.create_table(
        'exercises',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('target_reps', sa.Integer, nullable=False, default=15),
        sa.Column('duration_seconds', sa.Integer, nullable=False, default=300),

        # Base exercise type for tracking (determines angle calculation)
        sa.Column('base_exercise_type', sa.String(50)),

        # Thresholds
        sa.Column('down_threshold', sa.Float),
        sa.Column('up_threshold', sa.Float),
        sa.Column('hysteresis', sa.Float, default=5.0),

        # Metadata
        sa.Column('difficulty_level', sa.String(50)),
        sa.Column('primary_muscle_group', sa.String(100)),
        sa.Column('video_path', sa.String(500)),
        sa.Column('thumbnail_path', sa.String(500)),

        # Tracking
        sa.Column('created_by_doctor_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow)
    )

    # Create pending_exercises table
    op.create_table(
        'pending_exercises',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('doctor_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),

        # Video
        sa.Column('video_path', sa.String(500), nullable=False),
        sa.Column('thumbnail_path', sa.String(500)),
        sa.Column('video_duration_seconds', sa.Integer),

        # AI Results (JSON)
        sa.Column('detected_exercise_type', sa.String(100)),
        sa.Column('detected_thresholds', sa.Text),
        sa.Column('movement_signature', sa.Text),
        sa.Column('confidence_score', sa.Float),

        # Doctor Input
        sa.Column('manual_exercise_name', sa.String(255)),
        sa.Column('manual_description', sa.Text),
        sa.Column('manual_thresholds', sa.Text),

        # Status
        sa.Column('status', sa.String(50), nullable=False, default='UPLOADING'),
        sa.Column('error_message', sa.Text),

        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.utcnow)
    )

    # Create exercise_angle_rules table
    op.create_table(
        'exercise_angle_rules',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('exercise_id', sa.String(100), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('angle_name', sa.String(100), nullable=False),
        sa.Column('min_angle', sa.Float),
        sa.Column('max_angle', sa.Float),
        sa.Column('error_message', sa.String(255)),
        sa.Column('error_severity', sa.String(50))
    )

    # Insert default exercises (migrate from hardcoded)
    # For default exercises, base_exercise_type = id (they are the base types themselves)
    op.execute("""
        INSERT INTO exercises (id, name, description, target_reps, duration_seconds,
                             base_exercise_type, down_threshold, up_threshold, hysteresis,
                             difficulty_level, primary_muscle_group, video_path,
                             is_default, is_active, created_at, updated_at)
        VALUES
        ('squat', 'Squat (Gập gối)', 'Bài tập tăng cường cơ chân và khớp gối',
         16, 600, 'squat', 160.0, 90.0, 5.0,
         'medium', 'legs', '/squat.mp4',
         1, 1, datetime('now'), datetime('now')),

        ('arm_raise', 'Nâng Tay', 'Bài tập tăng cường cơ vai và tay',
         12, 300, 'arm_raise', 90.0, 160.0, 5.0,
         'easy', 'shoulders', '/arm_raise.mp4',
         1, 1, datetime('now'), datetime('now')),

        ('calf_raise', 'Nâng Gót Chân', 'Bài tập tăng cường cơ bắp chân',
         12, 300, 'calf_raise', 120.0, 140.0, 5.0,
         'easy', 'calves', '/calf_raise.mp4',
         1, 1, datetime('now'), datetime('now')),

        ('single_leg_stand', 'Đứng 1 Chân', 'Bài tập cân bằng và tăng cường cơ chân',
         10, 300, 'single_leg_stand', NULL, NULL, 5.0,
         'medium', 'legs', '/single_leg_stand.mp4',
         1, 1, datetime('now'), datetime('now'))
    """)


def downgrade():
    op.drop_table('exercise_angle_rules')
    op.drop_table('pending_exercises')
    op.drop_table('exercises')
