# Profile router
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from models import User, Gender, MobilityLevel, UserExerciseLimits, get_db
from routers.auth import verify_token
from ai_models import PersonalizationEngine
from limiter import limiter

router = APIRouter()

# Initialize AI Personalization Engine
personalization_engine = PersonalizationEngine()

class UpdateProfileRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_conditions: Optional[str] = None
    mobility_level: Optional[str] = None
    pain_level: Optional[int] = None
    injury_type: Optional[str] = None

class PersonalizedParamsRequest(BaseModel):
    exercise_type: str

@router.post("/update")
@limiter.limit("10/minute")
async def update_profile(
    request: Request,
    profile_req: UpdateProfileRequest,
    credentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update user profile with biometric and medical data"""
    user_id = credentials['user_id']

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate BMI if height and weight provided
    bmi = None
    if profile_req.height_cm and profile_req.weight_kg:
        bmi = profile_req.weight_kg / ((profile_req.height_cm / 100) ** 2)

    # Update user profile
    if profile_req.age is not None:
        user.age = profile_req.age

    if profile_req.gender:
        user.gender = Gender(profile_req.gender)

    if profile_req.height_cm is not None:
        user.height_cm = profile_req.height_cm

    if profile_req.weight_kg is not None:
        user.weight_kg = profile_req.weight_kg

    if bmi is not None:
        user.bmi = bmi

    if profile_req.medical_conditions is not None:
        user.medical_conditions = profile_req.medical_conditions

    if profile_req.mobility_level:
        user.mobility_level = MobilityLevel(profile_req.mobility_level)

    if profile_req.pain_level is not None:
        user.pain_level = profile_req.pain_level

    if profile_req.injury_type is not None:
        user.injury_type = profile_req.injury_type

    db.commit()

    return {
        'success': True,
        'message': 'Profile updated successfully',
        'bmi': round(bmi, 1) if bmi else None
    }

@router.get("/me")
@limiter.limit("60/minute")
async def get_my_profile(request: Request, credentials = Depends(verify_token), db: Session = Depends(get_db)):
    """Get current user's profile"""
    user_id = credentials['user_id']

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'age': user.age,
        'gender': user.gender.value if user.gender else None,
        'height_cm': user.height_cm,
        'weight_kg': user.weight_kg,
        'bmi': user.bmi,
        'medical_conditions': user.medical_conditions,
        'injury_type': user.injury_type,
        'mobility_level': user.mobility_level.value if user.mobility_level else None,
        'pain_level': user.pain_level,
        'doctor_notes': user.doctor_notes,
        'contraindicated_exercises': user.contraindicated_exercises,
        'role': user.role.value
    }

@router.post("/personalized-params")
@limiter.limit("20/minute")
async def get_personalized_params(
    request: Request,
    params_req: PersonalizedParamsRequest,
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
        params_req.exercise_type
    )

    # Save to database
    existing_limit = db.query(UserExerciseLimits).filter(
        UserExerciseLimits.user_id == user_id,
        UserExerciseLimits.exercise_type == params_req.exercise_type
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
            exercise_type=params_req.exercise_type,
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
