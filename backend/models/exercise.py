from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Exercise(Base):
    """
    Exercises table - stores all available exercises (default + custom)
    """
    __tablename__ = "exercises"

    id = Column(String(100), primary_key=True)  # e.g., "squat", "custom_knee_flex_123"
    name = Column(String(255), nullable=False)  # e.g., "Bài Tập Squat"
    description = Column(Text)  # "Bài tập tăng cường cơ chân"
    target_reps = Column(Integer, nullable=False, default=15)
    duration_seconds = Column(Integer, nullable=False, default=300)

    # Base exercise type for tracking (squat, arm_raise, calf_raise, single_leg_stand)
    # For custom exercises, this determines which angle calculation and state machine to use
    base_exercise_type = Column(String(50))  # e.g., "squat" for a custom squat variation

    # Thresholds (nullable - some exercises may not need)
    down_threshold = Column(Float)  # e.g., 160.0 for squat (standing position)
    up_threshold = Column(Float)    # e.g., 90.0 for squat (deep squat position)
    hysteresis = Column(Float, default=5.0)

    # Metadata
    difficulty_level = Column(String(50))       # "beginner", "intermediate", "advanced"
    primary_muscle_group = Column(String(100))  # "legs", "shoulders", "calves"
    video_path = Column(String(500))            # "/static/videos/squat.mp4"
    thumbnail_path = Column(String(500))        # "/static/thumbnails/squat.jpg"

    # Tracking
    created_by_doctor_id = Column(Integer, ForeignKey('users.id'))
    is_default = Column(Boolean, default=False)  # Built-in vs custom exercise
    is_active = Column(Boolean, default=True)    # Can be disabled without deleting
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by_doctor_id])
    angle_rules = relationship("ExerciseAngleRule", back_populates="exercise", cascade="all, delete-orphan")


class PendingExercise(Base):
    """
    Pending exercises awaiting doctor approval
    """
    __tablename__ = "pending_exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Video info
    video_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    video_duration_seconds = Column(Integer)

    # AI Recognition Results (JSON fields)
    detected_exercise_type = Column(String(100))  # "squat", "arm_raise", "unknown"
    detected_thresholds = Column(Text)            # JSON: {"down_angle": 160, "up_angle": 90}
    movement_signature = Column(Text)             # JSON: Movement patterns, angle ranges
    confidence_score = Column(Float)              # 0-1: How confident is AI

    # Doctor Input (manual overrides)
    manual_exercise_name = Column(String(255))    # Doctor can override AI suggestion
    manual_description = Column(Text)
    manual_thresholds = Column(Text)              # JSON: Doctor adjustments

    # Processing status
    status = Column(String(50), nullable=False, default='UPLOADING')
    # Status values: UPLOADING, PROCESSING, PENDING, APPROVED, REJECTED, ERROR
    error_message = Column(Text)  # If processing failed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    doctor = relationship("User", foreign_keys=[doctor_id])


class ExerciseAngleRule(Base):
    """
    Configurable angle rules for error detection per exercise
    (Optional - for future customization)
    """
    __tablename__ = "exercise_angle_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(String(100), ForeignKey('exercises.id'), nullable=False)
    angle_name = Column(String(100), nullable=False)  # "left_knee", "right_shoulder"
    min_angle = Column(Float)                         # Minimum acceptable angle
    max_angle = Column(Float)                         # Maximum acceptable angle
    error_message = Column(String(255))               # Message when violated
    error_severity = Column(String(50))               # "low", "medium", "high"

    # Relationships
    exercise = relationship("Exercise", back_populates="angle_rules")
