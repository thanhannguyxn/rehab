# Doctor router
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional, Dict, Any
import os
import uuid
import json
import shutil
import threading

from models import User, UserRole, DBSession, SessionError, SessionFrame, PendingExercise, Exercise, ExerciseAngleRule, ProgressionSuggestion, PatientExerciseAssignment, get_db
from routers.auth import get_current_user
from limiter import limiter
from services.progression_service import apply_suggestion
from db.connection import SessionLocal
from fastapi_cache.decorator import cache
from sqlalchemy.orm import selectinload

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

SUPPORTED_BASE_EXERCISE_TYPES = {"squat", "arm_raise", "calf_raise", "single_leg_stand"}


def _default_thresholds_for(base_exercise_type: str) -> Dict[str, float]:
    defaults = {
        "squat": {"down_threshold": 160.0, "up_threshold": 90.0, "hysteresis": 5.0},
        "arm_raise": {"down_threshold": 90.0, "up_threshold": 160.0, "hysteresis": 5.0},
        "calf_raise": {"down_threshold": 120.0, "up_threshold": 140.0, "hysteresis": 5.0},
        "single_leg_stand": {"down_threshold": 160.0, "up_threshold": 50.0, "hysteresis": 5.0},
    }
    return defaults.get(base_exercise_type, defaults["squat"])


def _resolve_supported_base_type(
    detected_type: Optional[str],
    movement_signature: Dict[str, Any],
) -> str:
    """
    Map AI output to one supported tracking type to keep websocket tracking stable.
    """
    detected = (detected_type or "").strip().lower()
    if detected in SUPPORTED_BASE_EXERCISE_TYPES:
        return detected

    aliases = {
        "armraise": "arm_raise",
        "raise_arm": "arm_raise",
        "shoulder_raise": "arm_raise",
        "heel_raise": "calf_raise",
        "singlelegstand": "single_leg_stand",
        "one_leg_stand": "single_leg_stand",
    }
    if detected in aliases:
        return aliases[detected]

    if any(token in detected for token in ["single", "one_leg", "one-leg", "balance"]):
        return "single_leg_stand"
    if any(token in detected for token in ["calf", "heel", "ankle", "toe_raise", "toe-raise"]):
        return "calf_raise"
    if any(token in detected for token in ["arm", "shoulder", "raise", "overhead"]):
        return "arm_raise"
    if any(token in detected for token in ["squat", "knee", "hip", "lunge", "sit"]):
        return "squat"

    tracking_logic = movement_signature.get("tracking_logic") or {}
    tracking_base = str(tracking_logic.get("base_exercise_type", "")).strip().lower()
    if tracking_base in SUPPORTED_BASE_EXERCISE_TYPES:
        return tracking_base

    primary_joints = movement_signature.get("primary_joints") or []
    joints = {str(j).strip().lower() for j in primary_joints}
    if "shoulder" in joints or "elbow" in joints:
        return "arm_raise"
    if "ankle" in joints or "foot" in joints:
        return "calf_raise"
    if "hip" in joints or "knee" in joints:
        return "squat"

    return "squat"


def _normalize_thresholds(raw_thresholds: Dict[str, Any], base_exercise_type: str) -> Dict[str, float]:
    defaults = _default_thresholds_for(base_exercise_type)
    down_threshold = raw_thresholds.get("down_threshold")
    up_threshold = raw_thresholds.get("up_threshold")

    # Backward compatibility for old payload keys.
    if down_threshold is None:
        down_threshold = raw_thresholds.get("down_angle")
    if up_threshold is None:
        up_threshold = raw_thresholds.get("up_angle")

    hysteresis = raw_thresholds.get("hysteresis", defaults["hysteresis"])

    return {
        "down_threshold": float(down_threshold) if down_threshold is not None else defaults["down_threshold"],
        "up_threshold": float(up_threshold) if up_threshold is not None else defaults["up_threshold"],
        "hysteresis": float(hysteresis) if hysteresis is not None else defaults["hysteresis"],
    }


def _create_angle_rules_from_tracking_logic(
    db: Session,
    exercise_id: str,
    movement_signature: Dict[str, Any],
) -> None:
    tracking_logic = movement_signature.get("tracking_logic") or {}
    raw_rules = tracking_logic.get("angle_rules") or []

    if not isinstance(raw_rules, list):
        return

    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue

        angle_name = str(raw_rule.get("angle_name", "")).strip()
        if not angle_name:
            continue

        min_angle = raw_rule.get("min_angle")
        max_angle = raw_rule.get("max_angle")
        error_message = str(raw_rule.get("error_message") or "Goc khop vuot nguong")
        error_severity = str(raw_rule.get("error_severity") or "medium").lower()
        if error_severity not in {"low", "medium", "high"}:
            error_severity = "medium"

        db.add(ExerciseAngleRule(
            exercise_id=exercise_id,
            angle_name=angle_name,
            min_angle=float(min_angle) if min_angle is not None else None,
            max_angle=float(max_angle) if max_angle is not None else None,
            error_message=error_message,
            error_severity=error_severity,
        ))

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

    patients = db.query(User).filter(
        User.role == UserRole.patient,
        User.doctor_id == current_user['user_id']
    ).order_by(User.full_name).all()

    patient_ids = [p.id for p in patients]

    # Get latest session for each patient efficiently
    subquery = db.query(
        DBSession.patient_id,
        func.max(DBSession.start_time).label('max_time')
    ).filter(DBSession.patient_id.in_(patient_ids)).group_by(DBSession.patient_id).subquery()

    latest_sessions_query = db.query(DBSession).join(
        subquery,
        (DBSession.patient_id == subquery.c.patient_id) & 
        (DBSession.start_time == subquery.c.max_time)
    ).all()

    latest_sessions_map = {s.patient_id: s for s in latest_sessions_query}

    result = []
    for patient in patients:
        last_session = latest_sessions_map.get(patient.id)

        result.append({
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

    return {'patients': result}

@router.get("/patient/{patient_id}/history")
@limiter.limit("30/minute")
async def get_patient_history(request: Request, patient_id: int, limit: int = 20, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    sessions_query = db.query(DBSession).options(
        selectinload(DBSession.errors)
    ).filter(
        DBSession.patient_id == patient_id
    ).order_by(DBSession.start_time.desc()).limit(limit).all()

    # Build display name lookup from Exercise table for custom exercises
    exercise_ids = {s.exercise_name for s in sessions_query}
    ex_name_map: dict = {}
    if exercise_ids:
        rows = db.query(Exercise.id, Exercise.name).filter(Exercise.id.in_(exercise_ids)).all()
        ex_name_map = {row.id: row.name for row in rows}

    def _ex_display_name(eid: str) -> str:
        return ex_name_map.get(eid) or get_vietnamese_exercise_name(eid)

    sessions = []
    for session in sessions_query:
        # Get errors using preloaded relationship to avoid N+1 query
        error_list = [{'name': get_vietnamese_error_name(e.error_name), 'count': e.count, 'severity': e.severity} for e in session.errors]

        sessions.append({
            'id': session.id,
            'exercise_name': _ex_display_name(session.exercise_name),
            'start_time': (session.start_time.isoformat() if isinstance(session.start_time, datetime) else datetime.fromisoformat(session.start_time.replace('Z', '+00:00')).isoformat()) if session.start_time else None,
            'total_reps': session.total_reps,
            'correct_reps': session.correct_reps,
            'accuracy': session.accuracy,
            'duration_seconds': session.duration_seconds,
            'errors': error_list,
            'avg_pain_level': session.avg_pain_level,
            'avg_fatigue_level': session.avg_fatigue_level,
            'predominant_emotion': session.predominant_emotion,
            'pain_incidents': session.pain_incidents,
            'fatigue_incidents': session.fatigue_incidents,
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


# ============================================================
# EXERCISE MANAGEMENT ENDPOINTS
# ============================================================

UPLOAD_DIR = "uploads/videos"
THUMBNAIL_DIR = "uploads/thumbnails"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def run_video_analysis_in_thread(pending_id: int, file_path: str):
    """Run video analysis in a separate thread"""
    from services.video_analysis_task import analyze_video_task
    analyze_video_task(pending_id, file_path, SessionLocal)


@router.post("/exercises/upload")
@limiter.limit("5/minute")
async def upload_exercise_video(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload video for exercise recognition"""

    # 1. Validate user is doctor
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền upload")

    # 2. Validate file type
    allowed_extensions = ('.mp4', '.avi', '.mov', '.webm')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file video (mp4, avi, mov, webm)")

    # 3. Read file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File quá lớn (tối đa 100MB)")

    # 4. Save file
    doctor_id = current_user['user_id']
    upload_dir = f"{UPLOAD_DIR}/{doctor_id}"
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
    file_path = f"{upload_dir}/{safe_filename}"

    with open(file_path, 'wb') as f:
        f.write(contents)

    # 5. Create pending exercise record
    pending = PendingExercise(
        doctor_id=doctor_id,
        video_path=file_path,
        status='UPLOADING'
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    # 6. Trigger video analysis in background thread
    thread = threading.Thread(
        target=run_video_analysis_in_thread,
        args=(pending.id, file_path)
    )
    thread.start()

    return {
        'success': True,
        'pending_id': pending.id,
        'message': 'Video đã upload. Đang phân tích...'
    }


@router.get("/exercises/pending")
@limiter.limit("30/minute")
async def get_pending_exercises(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending exercises for current doctor"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền xem")

    pending_list = db.query(PendingExercise).filter(
        PendingExercise.doctor_id == current_user['user_id']
    ).order_by(PendingExercise.created_at.desc()).all()

    return {
        'pending_exercises': [
            {
                'id': p.id,
                'video_path': p.video_path,
                'thumbnail_path': p.thumbnail_path,
                'status': p.status,
                'detected_type': p.detected_exercise_type,
                'confidence': p.confidence_score,
                'error_message': p.error_message,
                'created_at': p.created_at.isoformat() if p.created_at else None
            }
            for p in pending_list
        ]
    }


@router.get("/exercises/pending/{pending_id}")
@limiter.limit("30/minute")
async def get_pending_exercise_detail(
    request: Request,
    pending_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis results for pending exercise"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền xem")

    pending = db.query(PendingExercise).filter(
        PendingExercise.id == pending_id,
        PendingExercise.doctor_id == current_user['user_id']
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    # Parse JSON fields
    thresholds = {}
    signature = {}
    if pending.detected_thresholds:
        try:
            thresholds = json.loads(pending.detected_thresholds)
        except:
            pass
    if pending.movement_signature:
        try:
            signature = json.loads(pending.movement_signature)
        except:
            pass

    return {
        'id': pending.id,
        'video_path': pending.video_path,
        'thumbnail_path': pending.thumbnail_path,
        'video_duration_seconds': pending.video_duration_seconds,
        'detected_exercise_type': pending.detected_exercise_type,
        'detected_thresholds': thresholds,
        'movement_signature': signature,
        'confidence_score': pending.confidence_score,
        'manual_exercise_name': pending.manual_exercise_name,
        'manual_description': pending.manual_description,
        'status': pending.status,
        'error_message': pending.error_message,
        'created_at': pending.created_at.isoformat() if pending.created_at else None
    }


@router.put("/exercises/pending/{pending_id}")
@limiter.limit("30/minute")
async def update_pending_exercise(
    request: Request,
    pending_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Doctor manually adjusts AI results"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền chỉnh sửa")

    pending = db.query(PendingExercise).filter(
        PendingExercise.id == pending_id,
        PendingExercise.doctor_id == current_user['user_id']
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    # Get request body
    body = await request.json()

    # Update manual fields
    if 'manual_exercise_name' in body:
        pending.manual_exercise_name = body['manual_exercise_name']
    if 'manual_description' in body:
        pending.manual_description = body['manual_description']
    if 'manual_thresholds' in body:
        pending.manual_thresholds = json.dumps(body['manual_thresholds'])

    pending.updated_at = datetime.utcnow()
    db.commit()

    return {'success': True}


@router.post("/exercises/approve/{pending_id}")
@limiter.limit("10/minute")
async def approve_pending_exercise(
    request: Request,
    pending_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve pending exercise and create Exercise record"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền duyệt")

    pending = db.query(PendingExercise).filter(
        PendingExercise.id == pending_id,
        PendingExercise.doctor_id == current_user['user_id']
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    if pending.status not in ['PENDING', 'ERROR']:
        raise HTTPException(status_code=400, detail=f"Không thể duyệt bài tập có trạng thái {pending.status}")

    # Use manual values if provided, otherwise use AI detected values
    exercise_name = pending.manual_exercise_name or pending.detected_exercise_type or 'custom_exercise'
    exercise_desc = pending.manual_description or ''

    # Parse thresholds
    thresholds: Dict[str, Any] = {}
    if pending.manual_thresholds:
        try:
            thresholds = json.loads(pending.manual_thresholds)
        except:
            pass
    elif pending.detected_thresholds:
        try:
            thresholds = json.loads(pending.detected_thresholds)
        except:
            pass

    # Parse movement signature for description/instructions
    signature = {}
    if pending.movement_signature:
        try:
            signature = json.loads(pending.movement_signature)
        except:
            pass

    # Always persist a supported base type so realtime angle tracking can work for custom IDs.
    base_exercise_type = _resolve_supported_base_type(pending.detected_exercise_type, signature)
    thresholds = _normalize_thresholds(thresholds, base_exercise_type)

    if not exercise_desc and 'description' in signature:
        exercise_desc = signature.get('description', '')

    # Generate unique exercise ID
    exercise_id = f"custom_{exercise_name.lower().replace(' ', '_')}_{pending.id}"

    # If video was already uploaded to Cloudinary, use that URL directly
    if pending.video_path and pending.video_path.startswith("https://"):
        production_video_path = pending.video_path
    else:
        production_video_path = f"/uploads/videos/{pending.doctor_id}/{os.path.basename(pending.video_path)}"

    # Create Exercise — start conservative so patients can build up via progression
    new_exercise = Exercise(
        id=exercise_id,
        name=exercise_name,
        description=exercise_desc,
        target_reps=8,
        duration_seconds=180,
        base_exercise_type=base_exercise_type,  # For tracking - determines angle calculation
        down_threshold=thresholds['down_threshold'],
        up_threshold=thresholds['up_threshold'],
        hysteresis=thresholds['hysteresis'],
        difficulty_level='medium',
        video_path=production_video_path,
        thumbnail_path=pending.thumbnail_path,
        created_by_doctor_id=pending.doctor_id,
        is_default=False,
        is_active=True
    )

    db.add(new_exercise)

    # Persist OpenAI-generated tracking angle rules for this exercise.
    _create_angle_rules_from_tracking_logic(db, exercise_id, signature)

    # Update pending status
    pending.status = 'APPROVED'
    pending.updated_at = datetime.utcnow()

    db.commit()

    return {
        'success': True,
        'exercise_id': exercise_id,
        'message': 'Bài tập đã được thêm vào hệ thống!'
    }


@router.delete("/exercises/pending/{pending_id}")
@limiter.limit("30/minute")
async def reject_pending_exercise(
    request: Request,
    pending_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject and delete pending exercise"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền từ chối")

    pending = db.query(PendingExercise).filter(
        PendingExercise.id == pending_id,
        PendingExercise.doctor_id == current_user['user_id']
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    # Delete video files
    try:
        if pending.video_path and os.path.exists(pending.video_path):
            os.remove(pending.video_path)
        if pending.thumbnail_path and os.path.exists(pending.thumbnail_path):
            os.remove(pending.thumbnail_path)
    except Exception as e:
        print(f"Error deleting files: {e}")

    # Delete pending record
    db.delete(pending)
    db.commit()

    return {'success': True, 'message': 'Đã xóa bài tập'}


@router.post("/exercises/reanalyze/{pending_id}")
@limiter.limit("5/minute")
async def reanalyze_pending_exercise(
    request: Request,
    pending_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-trigger analysis for a pending exercise that had an error"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền phân tích lại")

    pending = db.query(PendingExercise).filter(
        PendingExercise.id == pending_id,
        PendingExercise.doctor_id == current_user['user_id']
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Không tìm thấy")

    if pending.status not in ['ERROR', 'PENDING']:
        raise HTTPException(status_code=400, detail="Chỉ có thể phân tích lại bài tập có lỗi hoặc đang chờ")

    # Reset status and trigger re-analysis
    pending.status = 'UPLOADING'
    pending.error_message = None
    pending.updated_at = datetime.utcnow()
    db.commit()

    # Trigger analysis in background
    thread = threading.Thread(
        target=run_video_analysis_in_thread,
        args=(pending.id, pending.video_path)
    )
    thread.start()

    return {
        'success': True,
        'message': 'Đang phân tích lại video...'
    }


# ============================================================
# APPROVED EXERCISES MANAGEMENT
# ============================================================

# Mapping from base_exercise_type to tracked angles
BASE_EXERCISE_ANGLES = {
    "squat": {
        "primary_angles": ["left_knee", "right_knee"],
        "angle_names_vi": {
            "left_knee": "Gối trái",
            "right_knee": "Gối phải"
        },
        "description": "Góc gối: HIP → KNEE → ANKLE"
    },
    "arm_raise": {
        "primary_angles": ["left_shoulder", "right_shoulder"],
        "angle_names_vi": {
            "left_shoulder": "Vai trái",
            "right_shoulder": "Vai phải"
        },
        "description": "Góc vai: HIP → SHOULDER → ELBOW"
    },
    "calf_raise": {
        "primary_angles": ["left_ankle", "right_ankle"],
        "angle_names_vi": {
            "left_ankle": "Cổ chân trái",
            "right_ankle": "Cổ chân phải"
        },
        "description": "Góc cổ chân: KNEE → ANKLE → FOOT"
    },
    "single_leg_stand": {
        "primary_angles": ["left_knee", "right_knee"],
        "angle_names_vi": {
            "left_knee": "Gối trái",
            "right_knee": "Gối phải"
        },
        "description": "Góc gối khi đứng một chân"
    }
}


@router.get("/exercises")
@limiter.limit("30/minute")
@cache(expire=3600)  # Cache exercises for 1 hour to reduce DB load
async def get_doctor_exercises(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all approved exercises (custom exercises created by any doctor + default exercises)"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền xem")

    exercises = db.query(Exercise).filter(
        Exercise.is_active == True
    ).order_by(Exercise.is_default.desc(), Exercise.created_at.desc()).all()

    result = []
    for ex in exercises:
        # Get angle rules for this exercise
        angle_rules = db.query(ExerciseAngleRule).filter(
            ExerciseAngleRule.exercise_id == ex.id
        ).all()

        # Get angle tracking info based on base_exercise_type
        angle_info = BASE_EXERCISE_ANGLES.get(ex.base_exercise_type, BASE_EXERCISE_ANGLES["squat"])

        result.append({
            'id': ex.id,
            'name': ex.name,
            'description': ex.description,
            'target_reps': ex.target_reps,
            'duration_seconds': ex.duration_seconds,
            'base_exercise_type': ex.base_exercise_type,
            'down_threshold': ex.down_threshold,
            'up_threshold': ex.up_threshold,
            'hysteresis': ex.hysteresis,
            'difficulty_level': ex.difficulty_level,
            'video_path': ex.video_path,
            'thumbnail_path': ex.thumbnail_path,
            'is_default': ex.is_default,
            'created_at': ex.created_at.isoformat() if ex.created_at else None,
            'angle_tracking': {
                'primary_angles': angle_info['primary_angles'],
                'angle_names_vi': angle_info['angle_names_vi'],
                'description': angle_info['description']
            },
            'angle_rules': [
                {
                    'id': rule.id,
                    'angle_name': rule.angle_name,
                    'min_angle': rule.min_angle,
                    'max_angle': rule.max_angle,
                    'error_message': rule.error_message,
                    'error_severity': rule.error_severity
                }
                for rule in angle_rules
            ]
        })

    return {'exercises': result}


@router.get("/exercises/{exercise_id}")
@limiter.limit("30/minute")
async def get_exercise_detail(
    request: Request,
    exercise_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about an exercise including angle tracking info"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền xem")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")

    # Get angle rules
    angle_rules = db.query(ExerciseAngleRule).filter(
        ExerciseAngleRule.exercise_id == exercise_id
    ).all()

    # Get angle tracking info
    angle_info = BASE_EXERCISE_ANGLES.get(exercise.base_exercise_type, BASE_EXERCISE_ANGLES["squat"])

    return {
        'id': exercise.id,
        'name': exercise.name,
        'description': exercise.description,
        'target_reps': exercise.target_reps,
        'duration_seconds': exercise.duration_seconds,
        'base_exercise_type': exercise.base_exercise_type,
        'down_threshold': exercise.down_threshold,
        'up_threshold': exercise.up_threshold,
        'hysteresis': exercise.hysteresis,
        'difficulty_level': exercise.difficulty_level,
        'primary_muscle_group': exercise.primary_muscle_group,
        'video_path': exercise.video_path,
        'thumbnail_path': exercise.thumbnail_path,
        'is_default': exercise.is_default,
        'created_at': exercise.created_at.isoformat() if exercise.created_at else None,
        'updated_at': exercise.updated_at.isoformat() if exercise.updated_at else None,
        'angle_tracking': {
            'primary_angles': angle_info['primary_angles'],
            'angle_names_vi': angle_info['angle_names_vi'],
            'description': angle_info['description']
        },
        'angle_rules': [
            {
                'id': rule.id,
                'angle_name': rule.angle_name,
                'min_angle': rule.min_angle,
                'max_angle': rule.max_angle,
                'error_message': rule.error_message,
                'error_severity': rule.error_severity
            }
            for rule in angle_rules
        ]
    }


@router.put("/exercises/{exercise_id}")
@limiter.limit("30/minute")
async def update_exercise(
    request: Request,
    exercise_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing exercise"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền chỉnh sửa")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")

    # Don't allow editing default exercises
    if exercise.is_default:
        raise HTTPException(status_code=403, detail="Không thể chỉnh sửa bài tập mặc định")

    body = await request.json()

    # Update allowed fields
    if 'name' in body and body['name']:
        exercise.name = body['name']
    if 'description' in body:
        exercise.description = body['description']
    if 'target_reps' in body and body['target_reps']:
        exercise.target_reps = int(body['target_reps'])
    if 'duration_seconds' in body and body['duration_seconds']:
        exercise.duration_seconds = int(body['duration_seconds'])
    if 'down_threshold' in body and body['down_threshold'] is not None:
        exercise.down_threshold = float(body['down_threshold'])
    if 'up_threshold' in body and body['up_threshold'] is not None:
        exercise.up_threshold = float(body['up_threshold'])
    if 'hysteresis' in body and body['hysteresis'] is not None:
        exercise.hysteresis = float(body['hysteresis'])
    if 'difficulty_level' in body:
        exercise.difficulty_level = body['difficulty_level']
    if 'base_exercise_type' in body and body['base_exercise_type'] in SUPPORTED_BASE_EXERCISE_TYPES:
        exercise.base_exercise_type = body['base_exercise_type']

    # Update angle rules if provided
    if 'angle_rules' in body and isinstance(body['angle_rules'], list):
        # Delete existing rules
        db.query(ExerciseAngleRule).filter(
            ExerciseAngleRule.exercise_id == exercise_id
        ).delete()

        # Add new rules
        for rule_data in body['angle_rules']:
            if not isinstance(rule_data, dict):
                continue
            angle_name = str(rule_data.get('angle_name', '')).strip()
            if not angle_name:
                continue

            db.add(ExerciseAngleRule(
                exercise_id=exercise_id,
                angle_name=angle_name,
                min_angle=float(rule_data['min_angle']) if rule_data.get('min_angle') is not None else None,
                max_angle=float(rule_data['max_angle']) if rule_data.get('max_angle') is not None else None,
                error_message=str(rule_data.get('error_message') or ''),
                error_severity=str(rule_data.get('error_severity') or 'medium')
            ))

    exercise.updated_at = datetime.utcnow()
    db.commit()

    return {'success': True, 'message': 'Đã cập nhật bài tập'}


@router.delete("/exercises/{exercise_id}")
@limiter.limit("30/minute")
async def delete_exercise(
    request: Request,
    exercise_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an exercise (soft delete by setting is_active=False)"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có quyền xóa")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài tập")

    if exercise.is_default:
        raise HTTPException(status_code=403, detail="Không thể xóa bài tập mặc định")

    # Soft delete
    exercise.is_active = False
    exercise.updated_at = datetime.utcnow()
    db.commit()

    return {'success': True, 'message': 'Đã xóa bài tập'}
# ================ EMOTION TRACKING ENDPOINTS ================

@router.get("/sessions/{session_id}/emotions")
async def get_session_emotions(session_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get emotion data and timeline for a specific session"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")
    # Get session to verify it exists
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get emotion frames (if any were saved)
    emotion_frames = db.query(SessionFrame).filter(
        SessionFrame.session_id == session_id,
        SessionFrame.emotion_state.isnot(None)
    ).order_by(SessionFrame.timestamp).all()

    # Build emotion timeline
    emotion_timeline = []
    for frame in emotion_frames:
        emotion_metrics = {}
        if frame.emotion_metrics:
            try:
                emotion_metrics = json.loads(frame.emotion_metrics)
            except:
                pass

        emotion_timeline.append({
            'timestamp': frame.timestamp.isoformat(),
            'emotion_state': frame.emotion_state,
            'confidence': frame.emotion_confidence,
            'pain_level': frame.pain_level,
            'fatigue_level': frame.fatigue_level,
            'rep_count': frame.rep_count,
            'metrics': emotion_metrics
        })

    # Session emotion summary
    emotion_summary = {
        'avg_pain_level': session.avg_pain_level,
        'avg_fatigue_level': session.avg_fatigue_level,
        'predominant_emotion': session.predominant_emotion,
        'pain_incidents': session.pain_incidents,
        'fatigue_incidents': session.fatigue_incidents,
        'total_frames': len(emotion_timeline)
    }

    return {
        'session_id': session_id,
        'patient_name': session.patient.full_name,
        'exercise_name': session.exercise_name,
        'start_time': session.start_time.isoformat(),
        'end_time': session.end_time.isoformat() if session.end_time else None,
        'emotion_summary': emotion_summary,
        'emotion_timeline': emotion_timeline
    }

@router.get("/patients/{patient_id}/emotion-trends")
async def get_patient_emotion_trends(patient_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get emotion trends over multiple sessions for a patient"""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")
    # Get recent sessions with emotion data
    sessions = db.query(DBSession).filter(
        DBSession.patient_id == patient_id,
        DBSession.end_time.isnot(None),
        DBSession.predominant_emotion.isnot(None)
    ).order_by(DBSession.start_time.desc()).limit(20).all()

    if not sessions:
        return {
            'patient_id': patient_id,
            'trends': [],
            'summary': {
                'total_sessions': 0,
                'avg_pain_level': 0,
                'avg_fatigue_level': 0,
                'most_common_emotion': None
            }
        }

    # Build trends data
    trends = []
    total_pain = 0
    total_fatigue = 0
    emotion_counts = {}

    for session in sessions:
        trends.append({
            'session_id': session.id,
            'date': session.start_time.strftime('%Y-%m-%d'),
            'exercise_name': session.exercise_name,
            'duration_minutes': round(session.duration_seconds / 60, 1),
            'predominant_emotion': session.predominant_emotion,
            'avg_pain_level': session.avg_pain_level or 0,
            'avg_fatigue_level': session.avg_fatigue_level or 0,
            'pain_incidents': session.pain_incidents or 0,
            'fatigue_incidents': session.fatigue_incidents or 0,
            'accuracy': session.accuracy
        })

        # Accumulate for summary
        if session.avg_pain_level:
            total_pain += session.avg_pain_level
        if session.avg_fatigue_level:
            total_fatigue += session.avg_fatigue_level
        if session.predominant_emotion:
            emotion_counts[session.predominant_emotion] = emotion_counts.get(session.predominant_emotion, 0) + 1

    # Calculate summary
    session_count = len(sessions)
    avg_pain = round(total_pain / session_count, 3) if session_count > 0 else 0
    avg_fatigue = round(total_fatigue / session_count, 3) if session_count > 0 else 0
    most_common_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None

    return {
        'patient_id': patient_id,
        'trends': trends,
        'summary': {
            'total_sessions': session_count,
            'avg_pain_level': avg_pain,
            'avg_fatigue_level': avg_fatigue,
            'most_common_emotion': most_common_emotion,
            'emotion_distribution': emotion_counts
        }
    }


# ============================================================
# PROGRESSION SUGGESTIONS ENDPOINTS
# ============================================================

@router.get("/progression-suggestions")
@limiter.limit("30/minute")
async def list_progression_suggestions(
    request: Request,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all progression suggestions for patients under this doctor."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    query = db.query(ProgressionSuggestion).filter(
        ProgressionSuggestion.doctor_id == current_user['user_id']
    )
    if status:
        query = query.filter(ProgressionSuggestion.status == status)

    suggestions = query.order_by(ProgressionSuggestion.created_at.desc()).limit(50).all()

    patient_ids = list({s.patient_id for s in suggestions})
    patients = {
        p.id: p.full_name
        for p in db.query(User).filter(User.id.in_(patient_ids)).all()
    } if patient_ids else {}

    return {
        'suggestions': [
            {
                'id': s.id,
                'patient_id': s.patient_id,
                'patient_name': patients.get(s.patient_id, f'ID {s.patient_id}'),
                'exercise_name': s.exercise_name,
                'avg_accuracy': s.avg_accuracy,
                'trigger_session_count': s.trigger_session_count,
                'current_reps': s.current_reps,
                'suggested_reps': s.suggested_reps,
                'current_difficulty': s.current_difficulty,
                'suggested_difficulty': s.suggested_difficulty,
                'current_rest_seconds': s.current_rest_seconds,
                'suggested_rest_seconds': s.suggested_rest_seconds,
                'status': s.status,
                'doctor_note': s.doctor_note,
                'created_at': s.created_at.isoformat() if s.created_at else None,
            }
            for s in suggestions
        ]
    }


@router.post("/progression-suggestions/{suggestion_id}/approve")
@limiter.limit("20/minute")
async def approve_progression_suggestion(
    request: Request,
    suggestion_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve a progression suggestion → immediately updates UserExerciseLimits."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    suggestion = db.query(ProgressionSuggestion).filter(
        ProgressionSuggestion.id == suggestion_id,
        ProgressionSuggestion.doctor_id == current_user['user_id'],
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    if suggestion.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Đề xuất đã ở trạng thái '{suggestion.status}'")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    apply_suggestion(db, suggestion, doctor_note=body.get('note'))

    return {'ok': True, 'message': 'Đã duyệt và cập nhật giới hạn bài tập.'}


@router.post("/progression-suggestions/{suggestion_id}/reject")
@limiter.limit("20/minute")
async def reject_progression_suggestion(
    request: Request,
    suggestion_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a progression suggestion without changing exercise limits."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    suggestion = db.query(ProgressionSuggestion).filter(
        ProgressionSuggestion.id == suggestion_id,
        ProgressionSuggestion.doctor_id == current_user['user_id'],
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    if suggestion.status != 'pending':
        raise HTTPException(status_code=400, detail=f"Đề xuất đã ở trạng thái '{suggestion.status}'")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    suggestion.status = 'rejected'
    suggestion.doctor_note = body.get('note')
    suggestion.updated_at = datetime.utcnow()
    db.commit()

    return {'ok': True, 'message': 'Đã từ chối đề xuất.'}


# ============================================================
# EXERCISE ASSIGNMENT ENDPOINTS
# ============================================================

@router.get("/exercises/{exercise_id}/assignments")
@limiter.limit("30/minute")
async def get_exercise_assignments(
    request: Request,
    exercise_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List patients currently assigned to a custom exercise."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    assignments = (
        db.query(PatientExerciseAssignment)
        .filter(
            PatientExerciseAssignment.exercise_id == exercise_id,
            PatientExerciseAssignment.assigned_by == current_user['user_id'],
            PatientExerciseAssignment.is_active == True,
        )
        .all()
    )
    assigned_ids = {a.patient_id for a in assignments}

    # Return all doctor's patients with assigned flag
    patients = db.query(User).filter(
        User.doctor_id == current_user['user_id'],
        User.role == 'patient',
    ).all()

    return {
        'patients': [
            {
                'id': p.id,
                'full_name': p.full_name,
                'username': p.username,
                'assigned': p.id in assigned_ids,
            }
            for p in patients
        ]
    }


@router.post("/exercises/{exercise_id}/assign")
@limiter.limit("20/minute")
async def assign_exercise(
    request: Request,
    exercise_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign/unassign a custom exercise to a list of patients."""
    if current_user['role'] != 'doctor':
        raise HTTPException(status_code=403, detail="Doctors only")

    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise or exercise.is_default:
        raise HTTPException(status_code=400, detail="Chỉ có thể giao bài tập tùy chỉnh")

    body = await request.json()
    patient_ids: list[int] = body.get('patient_ids', [])
    note: str = body.get('note', '')

    # Deactivate all existing assignments for this exercise by this doctor
    db.query(PatientExerciseAssignment).filter(
        PatientExerciseAssignment.exercise_id == exercise_id,
        PatientExerciseAssignment.assigned_by == current_user['user_id'],
    ).update({'is_active': False})

    # Create new active assignments
    for pid in patient_ids:
        existing = db.query(PatientExerciseAssignment).filter(
            PatientExerciseAssignment.exercise_id == exercise_id,
            PatientExerciseAssignment.patient_id == pid,
        ).first()
        if existing:
            existing.is_active = True
            existing.note = note
            existing.assigned_by = current_user['user_id']
        else:
            db.add(PatientExerciseAssignment(
                patient_id=pid,
                exercise_id=exercise_id,
                assigned_by=current_user['user_id'],
                note=note,
                is_active=True,
            ))

    db.commit()
    return {'ok': True, 'assigned_count': len(patient_ids)}
