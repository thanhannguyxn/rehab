# General/public router for endpoints that don't need authentication or specific prefixes
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

import jwt
from models import User, Gender, MobilityLevel, UserExerciseLimits, Exercise, ProgressionSuggestion, get_db
from routers.auth import verify_token
from ai_models import PersonalizationEngine
from limiter import limiter
from settings import SECRET_KEY, ALGORITHM

router = APIRouter()

# Initialize AI Personalization Engine
personalization_engine = PersonalizationEngine()

class PersonalizedParamsRequest(BaseModel):
    exercise_type: str

@router.post("/personalized-params")
@limiter.limit("20/minute")
async def get_personalized_params(
    request: Request,
    req_data: PersonalizedParamsRequest,
    credentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get personalized exercise parameters based on user profile

    Returns customized angles, reps, rest time, warnings, and recommendations
    """
    user_id = credentials['user_id']

    # Get user data
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {
        'age': user.age,
        'gender': user.gender.value if user.gender else None,
        'height_cm': user.height_cm,
        'weight_kg': user.weight_kg,
        'bmi': user.bmi,
        'medical_conditions': user.medical_conditions,
        'injury_type': user.injury_type,
        'mobility_level': user.mobility_level.value if user.mobility_level else None,
        'pain_level': user.pain_level
    }

    # Calculate personalized parameters using AI engine
    params = personalization_engine.calculate_personalized_params(
        user_data,
        req_data.exercise_type
    )

    # Save to database
    existing_limit = db.query(UserExerciseLimits).filter(
        UserExerciseLimits.user_id == user_id,
        UserExerciseLimits.exercise_type == req_data.exercise_type
    ).first()

    # Check if doctor has approved a progression for this exercise — if so, preserve their reps value
    has_doctor_approved = db.query(ProgressionSuggestion).filter(
        ProgressionSuggestion.patient_id == user_id,
        ProgressionSuggestion.exercise_name == req_data.exercise_type,
        ProgressionSuggestion.status == "approved",
    ).first() is not None

    if existing_limit:
        existing_limit.max_depth_angle = params.get('down_angle')
        existing_limit.min_raise_angle = params.get('up_angle')
        if not has_doctor_approved:
            existing_limit.max_reps_per_set = params.get('max_reps')
            existing_limit.recommended_rest_seconds = params.get('rest_seconds')
            existing_limit.difficulty_score = params.get('difficulty_score')
        existing_limit.injury_risk_score = 0.0
        existing_limit.updated_at = datetime.utcnow()
    else:
        new_limit = UserExerciseLimits(
            user_id=user_id,
            exercise_type=req_data.exercise_type,
            max_depth_angle=params.get('down_angle'),
            min_raise_angle=params.get('up_angle'),
            max_reps_per_set=params.get('max_reps'),
            recommended_rest_seconds=params.get('rest_seconds'),
            difficulty_score=params.get('difficulty_score'),
            injury_risk_score=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_limit)

    db.commit()

    return params

# Exercise name mapping (English to Vietnamese)
EXERCISE_NAMES = {
    "squat": "Bài Tập Squat",
    "arm_raise": "Bài Tập Giơ Tay",
    "calf_raise": "Bài Tập Nâng Bắp Chân",
    "single_leg_stand": "Bài Tập Đứng Một Chân"
}

@router.get("/exercises")
@limiter.limit("30/minute")
async def get_exercises(request: Request, db: Session = Depends(get_db)):
    """Get active exercises, personalizing target_reps from UserExerciseLimits when authenticated."""
    exercises = db.query(Exercise).filter(
        Exercise.is_active == True
    ).order_by(Exercise.name).all()

    # Try to identify the calling patient to apply their progression limits
    patient_limits: dict[str, int] = {}
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ", 1)[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                rows = db.query(UserExerciseLimits).filter(
                    UserExerciseLimits.user_id == user_id,
                    UserExerciseLimits.max_reps_per_set.isnot(None),
                ).all()
                patient_limits = {
                    row.exercise_type: int(row.max_reps_per_set)
                    for row in rows
                }
        except Exception:
            pass  # unauthenticated or invalid token — use defaults

    def _personalized(ex: Exercise) -> tuple[int, int]:
        """Returns (target_reps, duration_seconds) personalized for this patient."""
        key = ex.base_exercise_type or ex.id
        if key in patient_limits and ex.target_reps:
            new_reps = patient_limits[key]
            # Scale duration proportionally with reps
            new_duration = max(60, round(ex.duration_seconds * new_reps / ex.target_reps))
            return new_reps, new_duration
        return ex.target_reps, ex.duration_seconds

    return {
        "exercises": [
            {
                "id": ex.id,
                "name": ex.name,
                "description": ex.description,
                **dict(zip(("target_reps", "duration_seconds"), _personalized(ex))),
                "difficulty_level": ex.difficulty_level,
                "video_path": ex.video_path,
                "thumbnail_path": ex.thumbnail_path,
                "base_exercise_type": ex.base_exercise_type,
                "is_default": ex.is_default
            }
            for ex in exercises
        ]
    }