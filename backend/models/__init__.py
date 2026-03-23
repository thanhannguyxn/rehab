"""
Models package for AI Rehabilitation System
"""

from .base import Base
from .user import User, UserRole, Gender, MobilityLevel, hash_password, verify_password
from .session import Session as DBSession, SessionFrame, SessionError, UserExerciseLimits, PatientSchedule

# Import database functions
from db.connection import get_db, init_db, engine, DATABASE_URL

__all__ = [
    'Base',
    'User', 'UserRole', 'Gender', 'MobilityLevel', 'hash_password', 'verify_password',
    'DBSession', 'SessionFrame', 'SessionError', 'UserExerciseLimits', 'PatientSchedule',
    'get_db', 'init_db', 'engine', 'DATABASE_URL'
]