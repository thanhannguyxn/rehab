from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from limiter import limiter
from models import User, UserRole, PatientSchedule, get_db
from routers.auth import get_current_user
from services.doctor_assistant_agent import generate_doctor_assistant_reply
from services.patient_coach_agent import generate_patient_coach_reply

router = APIRouter()


class PatientChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1500)
    exercise_type: Optional[str] = Field(default=None, max_length=100)


class DoctorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    patient_id: Optional[int] = Field(default=None, ge=1)


class NotificationReadResponse(BaseModel):
    ok: bool


@router.post("/patient/chat")
@limiter.limit("4/minute")
async def patient_chat(
    request: Request,
    payload: PatientChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patient users can access this endpoint")

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty")

    result = generate_patient_coach_reply(
        db=db,
        user_id=user_id,
        user_message=message,
        exercise_type=payload.exercise_type,
    )

    return {
        "reply": result.get("reply", ""),
        "safety_escalation": bool(result.get("safety_escalation", False)),
        "used_llm": bool(result.get("used_llm", False)),
    }


@router.post("/doctor/chat")
@limiter.limit("6/minute")
async def doctor_chat(
    request: Request,
    payload: DoctorChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="Only doctor users can access this endpoint")

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty")

    result = generate_doctor_assistant_reply(
        db=db,
        doctor_id=user_id,
        user_message=message,
        patient_id=payload.patient_id,
    )

    return {
        "reply": result.get("reply", ""),
        "used_llm": bool(result.get("used_llm", False)),
    }


@router.get("/patient/notifications")
@limiter.limit("20/minute")
async def get_patient_notifications(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patient users can access this endpoint")

    rows = (
        db.query(PatientSchedule, User.full_name)
        .join(User, User.id == PatientSchedule.doctor_id)
        .filter(PatientSchedule.patient_id == user_id, PatientSchedule.is_read == 0)
        .order_by(PatientSchedule.scheduled_for.asc(), PatientSchedule.created_at.desc())
        .limit(20)
        .all()
    )

    notifications = []
    for schedule, doctor_name in rows:
        notifications.append(
            {
                "id": schedule.id,
                "exercise_name": schedule.exercise_name,
                "scheduled_for": schedule.scheduled_for.isoformat() if schedule.scheduled_for else None,
                "doctor_name": doctor_name,
                "message": (
                    f"Dr. {doctor_name} scheduled {schedule.exercise_name} for "
                    f"{schedule.scheduled_for.strftime('%Y-%m-%d') if schedule.scheduled_for else 'upcoming session'}."
                ),
            }
        )

    return {"notifications": notifications}


@router.get("/patient/schedules")
@limiter.limit("20/minute")
async def get_patient_schedules(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patient users can access this endpoint")

    rows = (
        db.query(PatientSchedule, User.full_name)
        .join(User, User.id == PatientSchedule.doctor_id)
        .filter(PatientSchedule.patient_id == user_id)
        .order_by(PatientSchedule.scheduled_for.desc(), PatientSchedule.created_at.desc())
        .limit(100)
        .all()
    )

    schedules = []
    for schedule, doctor_name in rows:
        schedules.append(
            {
                "id": schedule.id,
                "exercise_name": schedule.exercise_name,
                "scheduled_for": schedule.scheduled_for.isoformat() if schedule.scheduled_for else None,
                "doctor_name": doctor_name,
                "note": schedule.note,
                "is_read": bool(schedule.is_read),
                "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            }
        )

    return {"schedules": schedules}


@router.post("/patient/notifications/{schedule_id}/read", response_model=NotificationReadResponse)
@limiter.limit("30/minute")
async def mark_patient_notification_read(
    request: Request,
    schedule_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Only patient users can access this endpoint")

    schedule = (
        db.query(PatientSchedule)
        .filter(PatientSchedule.id == schedule_id, PatientSchedule.patient_id == user_id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Notification not found")

    schedule.is_read = 1
    db.commit()

    return {"ok": True}
