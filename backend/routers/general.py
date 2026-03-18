# General/public router for endpoints that don't need authentication or specific prefixes
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from models import User, Gender, MobilityLevel, UserExerciseLimits, get_db
from routers.auth import verify_token
from ai_models import PersonalizationEngine

router = APIRouter()

# Initialize AI Personalization Engine
personalization_engine = PersonalizationEngine()

class PersonalizedParamsRequest(BaseModel):
    exercise_type: str

@router.post("/personalized-params")
async def get_personalized_params(
    request: PersonalizedParamsRequest,
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
        request.exercise_type
    )

    # Save to database
    existing_limit = db.query(UserExerciseLimits).filter(
        UserExerciseLimits.user_id == user_id,
        UserExerciseLimits.exercise_type == request.exercise_type
    ).first()

    if existing_limit:
        existing_limit.max_depth_angle = params.get('down_angle')
        existing_limit.min_raise_angle = params.get('up_angle')
        existing_limit.max_reps_per_set = params.get('max_reps')
        existing_limit.recommended_rest_seconds = params.get('rest_seconds')
        existing_limit.difficulty_score = params.get('difficulty_score')
        existing_limit.injury_risk_score = 0.0
        existing_limit.updated_at = datetime.utcnow()
    else:
        new_limit = UserExerciseLimits(
            user_id=user_id,
            exercise_type=request.exercise_type,
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
async def get_exercises():
    """Get available exercises - public endpoint"""
    return {
        "exercises": [
            {"id": "squat", "name": "Squat (Gập gối)", "description": "Bài tập tăng cường cơ chân", "target_reps": 16, "duration_seconds": 600},
            {"id": "arm_raise", "name": "Nâng Tay", "description": "Bài tập vai và tay", "target_reps": 12, "duration_seconds": 300},
            {"id": "single_leg_stand", "name": "Đứng 1 Chân", "description": "Bài tập cân bằng và cơ chân", "target_reps": 10, "duration_seconds": 300},
            {"id": "calf_raise", "name": "Nâng Gót Chân", "description": "Bài tập tăng cường cơ bắp chân", "target_reps": 12, "duration_seconds": 300}
        ]
    }