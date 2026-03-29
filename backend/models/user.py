# User model
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except Exception:
        pass
    import hashlib
    if hashed_password == hashlib.sha256(plain_password.encode()).hexdigest():
        return True
    return plain_password == hashed_password

class UserRole(enum.Enum):
    patient = "patient"
    doctor = "doctor"

class Gender(enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class MobilityLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

# Import Base from models
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(255))
    age = Column(Integer)
    gender = Column(Enum(Gender))
    height_cm = Column(Float)
    weight_kg = Column(Float)
    bmi = Column(Float)
    medical_conditions = Column(Text)
    injury_type = Column(Text)
    mobility_level = Column(Enum(MobilityLevel))
    pain_level = Column(Integer)
    doctor_notes = Column(Text)
    contraindicated_exercises = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True) # Add index for faster queries by created_at
    doctor_id = Column(Integer, ForeignKey('users.id'), index=True) # Add index for faster queries by doctor_id
    new_column = Column(String(100), nullable=True) #test for alembic migration

    # Relationships
    doctor = relationship("User", remote_side=[id])
    patients = relationship("User", back_populates="doctor")
    sessions = relationship("Session", back_populates="patient")
    exercise_limits = relationship("UserExerciseLimits", back_populates="user")

    __table_args__ = (
        CheckConstraint('pain_level BETWEEN 0 AND 10', name='check_pain_level'),
    )