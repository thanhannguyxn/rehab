# Sessions router
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from models import DBSession, SessionFrame, SessionError, get_db
from routers.auth import get_current_user
from services.session_runtime import start_live_session, get_live_session, pop_live_session
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

@router.post("/start")
@limiter.limit("20/minute")
async def start_session(request: Request, exercise_name: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # Create new session
    new_session = DBSession(
        patient_id=current_user['user_id'],
        exercise_name=exercise_name,
        start_time=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Initialize in-memory live stats for websocket-driven counting.
    start_live_session(new_session.id)

    return {'session_id': new_session.id}

@router.post("/{session_id}/end")
@limiter.limit("20/minute")
async def end_session(request: Request, session_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.patient_id == current_user['user_id']
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Calculate session stats
    frames = db.query(SessionFrame).filter(SessionFrame.session_id == session_id).all()

    start_time_dt = session.start_time
    if isinstance(start_time_dt, str):
        # Handle string parsing correctly
        start_time_dt = datetime.fromisoformat(start_time_dt.replace('Z', '+00:00')).replace(tzinfo=None)

    duration = (datetime.utcnow() - start_time_dt).total_seconds() if start_time_dt else 0
    total_reps = 0
    correct_reps = 0
    accuracy = 0.0

    if frames:
        total_reps = max((frame.rep_count for frame in frames), default=0)
        
        last_frame_dt = frames[-1].timestamp
        if isinstance(last_frame_dt, str):
            last_frame_dt = datetime.fromisoformat(last_frame_dt.replace('Z', '+00:00')).replace(tzinfo=None)
            
        duration = (last_frame_dt - start_time_dt).total_seconds()

        # Calculate accuracy based on error frames
        error_frames = [f for f in frames if f.errors and f.errors != '[]']
        correct_frames = len(frames) - len(error_frames)
        accuracy = (correct_frames / len(frames)) * 100 if frames else 0
        # We cannot infer per-rep correctness from frame-level data here.
        correct_reps = total_reps

    # Fallback to websocket runtime stats when frames are not persisted.
    live_stats = get_live_session(session_id)
    if live_stats and live_stats.get('total_reps', 0) >= total_reps:
        total_reps = int(live_stats.get('total_reps', 0))
        correct_reps = int(live_stats.get('correct_reps', 0))
        accuracy = float(live_stats.get('accuracy', 0.0))

    # Update session
    session.end_time = datetime.utcnow()
    session.total_reps = total_reps
    session.duration_seconds = int(duration)
    session.accuracy = round(accuracy, 2)
    session.correct_reps = correct_reps

    # Rebuild error summary from live stats if available.
    if live_stats:
        db.query(SessionError).filter(SessionError.session_id == session_id).delete()
        for error_name, count in live_stats.get('error_counts', {}).items():
            db.add(SessionError(
                session_id=session_id,
                error_name=error_name,
                count=count,
                severity='medium'
            ))
        db.flush()

    errors = db.query(SessionError).filter(SessionError.session_id == session_id).all()

    common_errors = {}
    for error in errors:
        vietnamese_name = get_vietnamese_error_name(error.error_name)
        common_errors[vietnamese_name] = {
            'count': error.count,
            'severity': error.severity or 'medium'
        }

    db.commit()
    pop_live_session(session_id)

    return {
        'session_id': session.id,
        'total_reps': total_reps,
        'correct_reps': correct_reps,
        'accuracy': round(accuracy, 2),
        'duration_seconds': int(duration),
        'common_errors': common_errors
    }

@router.get("/my-history")
@limiter.limit("30/minute")
async def get_my_history(request: Request, limit: int = 50, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions_query = db.query(DBSession).filter(
        DBSession.patient_id == current_user['user_id']
    ).order_by(DBSession.start_time.desc()).limit(limit).all()

    sessions = []
    for session in sessions_query:
        # Get errors for this session
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

@router.get("/error-analytics")
@limiter.limit("30/minute")
async def get_error_analytics(request: Request, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get error analytics grouped by exercise type"""
    from sqlalchemy import func

    # Get error statistics grouped by exercise type
    error_stats = db.query(
        DBSession.exercise_name,
        SessionError.error_name,
        func.sum(SessionError.count).label('total_count'),
        func.count(func.distinct(DBSession.id)).label('session_count')
    ).join(SessionError, DBSession.id == SessionError.session_id).filter(
        DBSession.patient_id == current_user['user_id']
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