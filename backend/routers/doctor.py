# Doctor router
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from models import User, UserRole, DBSession, SessionError, get_db
from routers.auth import get_current_user
from limiter import limiter

router = APIRouter()

# Exercise name mapping (English to Vietnamese)
EXERCISE_NAMES = {
    "squat": "Bài Tập Squat",
    "arm_raise": "Bài Tập Giơ Tay",
    "calf_raise": "Bài Tập Nâng Bắp Chân",
    "single_leg_stand": "Bài Tập Đứng Một Chân"
}

# Error name mapping (English to Vietnamese) - for legacy data
ERROR_NAMES = {
    # Arm raise errors
    "not_high": "Góc vai chưa đủ",
    "arms_bent": "Tay không thẳng",
    "not_low": "Chưa hạ hết",

    # Squat errors
    "not_deep": "Gập gối chưa đủ",
    "knees_forward": "Gối đẩy ra trước",
    "not_straight": "Chưa đứng thẳng",

    # Calf raise errors
    "not_raised": "Chưa nâng đủ cao",
    "knees_bent": "Gập gối",
    "not_lowered": "Chưa hạ hết",

    # Single leg stand errors
    "knee_not_bent": "Gối chưa gập đủ sâu",
    "leg_not_behind": "Chân không ra sau"
}

def get_vietnamese_exercise_name(exercise_type: str) -> str:
    """Convert exercise type to Vietnamese name"""
    return EXERCISE_NAMES.get(exercise_type, exercise_type)

def get_vietnamese_error_name(error_name: str) -> str:
    """Convert error name to Vietnamese - handles legacy English error names"""
    return ERROR_NAMES.get(error_name, error_name)

@router.get("/patients")
@limiter.limit("30/minute")
async def get_my_patients(request: Request, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    patients_query = db.query(User).filter(
        User.role == UserRole.patient,
        User.doctor_id == current_user['user_id']
    ).order_by(User.full_name).all()

    patients = []
    for patient in patients_query:
        # Get latest session
        last_session = db.query(DBSession).filter(
            DBSession.patient_id == patient.id
        ).order_by(DBSession.start_time.desc()).first()

        patients.append({
            'id': patient.id,
            'username': patient.username,
            'full_name': patient.full_name,
            'age': patient.age,
            'gender': patient.gender.value if patient.gender else None,
            'created_at': (patient.created_at.isoformat() if isinstance(patient.created_at, datetime) else datetime.fromisoformat(patient.created_at.replace('Z', '+00:00')).isoformat()) if patient.created_at else None,
            'last_session': {
                'date': (last_session.start_time.isoformat() if isinstance(last_session.start_time, datetime) else datetime.fromisoformat(last_session.start_time.replace('Z', '+00:00')).isoformat()) if last_session and last_session.start_time else None,
                'exercise': last_session.exercise_name if last_session else None,
                'accuracy': last_session.accuracy if last_session else None
            } if last_session else None
        })

    return {'patients': patients}

@router.get("/patient/{patient_id}/history")
@limiter.limit("30/minute")
async def get_patient_history(request: Request, patient_id: int, limit: int = 20, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    sessions_query = db.query(DBSession).filter(
        DBSession.patient_id == patient_id
    ).order_by(DBSession.start_time.desc()).limit(limit).all()

    sessions = []
    for session in sessions_query:
        # Get errors
        errors = db.query(SessionError).filter(SessionError.session_id == session.id).all()
        error_list = [{'name': get_vietnamese_error_name(e.error_name), 'count': e.count, 'severity': e.severity} for e in errors]

        sessions.append({
            'id': session.id,
            'exercise_name': get_vietnamese_exercise_name(session.exercise_name),
            'start_time': (session.start_time.isoformat() if isinstance(session.start_time, datetime) else datetime.fromisoformat(session.start_time.replace('Z', '+00:00')).isoformat()) if session.start_time else None,
            'total_reps': session.total_reps,
            'correct_reps': session.correct_reps,
            'accuracy': session.accuracy,
            'duration_seconds': session.duration_seconds,
            'errors': error_list
        })

    return {'sessions': sessions}

@router.get("/patient/{patient_id}/error-analytics")
@limiter.limit("30/minute")
async def get_patient_error_analytics(request: Request, patient_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get error analytics for a specific patient grouped by exercise type"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    from sqlalchemy import func

    # Get error statistics grouped by exercise type
    error_stats = db.query(
        DBSession.exercise_name,
        SessionError.error_name,
        func.sum(SessionError.count).label('total_count'),
        func.count(func.distinct(DBSession.id)).label('session_count')
    ).join(SessionError, DBSession.id == SessionError.session_id).filter(
        DBSession.patient_id == patient_id
    ).group_by(DBSession.exercise_name, SessionError.error_name).order_by(
        DBSession.exercise_name, func.sum(SessionError.count).desc()
    ).all()

    # Organize by exercise type and merge duplicate errors after Vietnamese translation
    analytics = {}
    for row in error_stats:
        exercise_name = row.exercise_name
        error_name = row.error_name
        total_count = row.total_count
        session_count = row.session_count

        # Convert to Vietnamese names
        vietnamese_exercise = get_vietnamese_exercise_name(exercise_name)
        vietnamese_error = get_vietnamese_error_name(error_name)

        if vietnamese_exercise not in analytics:
            analytics[vietnamese_exercise] = {
                'exercise_name': vietnamese_exercise,
                'errors': {}  # Use dict to merge duplicates
            }

        # Merge errors with same Vietnamese name
        if vietnamese_error not in analytics[vietnamese_exercise]['errors']:
            analytics[vietnamese_exercise]['errors'][vietnamese_error] = {
                'error_name': vietnamese_error,
                'total_count': 0,
                'session_count': 0
            }

        analytics[vietnamese_exercise]['errors'][vietnamese_error]['total_count'] += total_count
        analytics[vietnamese_exercise]['errors'][vietnamese_error]['session_count'] += session_count

    # Convert errors dict to list and calculate averages
    result = []
    for exercise in analytics.values():
        errors_list = []
        for error in exercise['errors'].values():
            errors_list.append({
                'error_name': error['error_name'],
                'total_count': error['total_count'],
                'session_count': error['session_count'],
                'avg_per_session': round(error['total_count'] / error['session_count'], 1) if error['session_count'] > 0 else 0
            })
        result.append({
            'exercise_name': exercise['exercise_name'],
            'errors': sorted(errors_list, key=lambda x: x['total_count'], reverse=True)
        })

    return {'analytics': result}