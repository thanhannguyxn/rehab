# Session model
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Import Base from models
from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    exercise_name = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    total_reps = Column(Integer, default=0)
    correct_reps = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    duration_seconds = Column(Integer, default=0)
    avg_heart_rate = Column(Integer)
    notes = Column(Text)

    # Relationships
    patient = relationship("User", back_populates="sessions")
    frames = relationship("SessionFrame", back_populates="session")
    errors = relationship("SessionError", back_populates="session")

class SessionFrame(Base):
    __tablename__ = "session_frames"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    rep_count = Column(Integer)
    angles = Column(Text)  # JSON string
    errors = Column(Text)  # JSON string

    # Relationships
    session = relationship("Session", back_populates="frames")

class SessionError(Base):
    __tablename__ = "session_errors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    error_name = Column(String(255), nullable=False)
    count = Column(Integer, default=0)
    severity = Column(String(50))

    # Relationships
    session = relationship("Session", back_populates="errors")

class UserExerciseLimits(Base):
    __tablename__ = "user_exercise_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exercise_type = Column(String(255), nullable=False)
    max_depth_angle = Column(Float)
    min_raise_angle = Column(Float)
    max_reps_per_set = Column(Integer)
    recommended_rest_seconds = Column(Integer)
    difficulty_score = Column(Float)
    injury_risk_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="exercise_limits")