"""Doctor assistant agent with doctor-scoped patient analytics context."""

import json
import re
import unicodedata
from datetime import timedelta
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User, DBSession, SessionError, UserRole, PatientSchedule
from services.patient_coach_agent import _call_chat_completion


_EXERCISE_ALIASES = {
    "arm_raise": ["arm_raise", "arm raise", "arm-raise", "giơ tay", "gio tay"],
    "squat": ["squat"],
    "calf_raise": ["calf_raise", "calf raise", "calf-raise", "nâng bắp chân", "nang bap chan"],
    "single_leg_stand": [
        "single_leg_stand",
        "single leg stand",
        "single-leg-stand",
        "đứng một chân",
        "dung mot chan",
    ],
}


def _normalize_text(text: str) -> str:
    lowered = (text or "").lower().replace("đ", "d")
    no_accents = "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )
    return " ".join(no_accents.split())


def _resolve_exercise_name(message: str) -> Optional[str]:
    normalized = _normalize_text(message)
    for canonical, aliases in _EXERCISE_ALIASES.items():
        if any(_normalize_text(alias) in normalized for alias in aliases):
            return canonical
    return None


def _resolve_scheduled_for(message: str) -> datetime:
    normalized = _normalize_text(message)

    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
    if date_match:
        try:
            return datetime.strptime(date_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    # Support dd/mm/yyyy and dd-mm-yyyy which are common in VN usage.
    date_match_dmy = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", normalized)
    if date_match_dmy:
        day = int(date_match_dmy.group(1))
        month = int(date_match_dmy.group(2))
        year = int(date_match_dmy.group(3))
        try:
            return datetime(year, month, day)
        except ValueError:
            pass

    now = datetime.utcnow()
    if "tomorrow" in normalized or "ngay mai" in normalized:
        target = now + timedelta(days=1)
        return datetime(target.year, target.month, target.day, 9, 0, 0)

    if "today" in normalized or "hom nay" in normalized:
        return datetime(now.year, now.month, now.day, 9, 0, 0)

    target = now + timedelta(days=1)
    return datetime(target.year, target.month, target.day, 9, 0, 0)


def _extract_patient_reference(message: str) -> Optional[str]:
    raw = (message or "").strip()
    match = re.search(r"(?:for|cho)\s+(.+)$", raw, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip(" .,!?:;\"'")


def _is_schedule_command(message: str) -> bool:
    normalized = _normalize_text(message)
    has_create = any(word in normalized for word in ["create", "tao", "lap", "schedule", "lich"])
    has_target = any(word in normalized for word in ["for", "cho"])
    return has_create and has_target and ("schedule" in normalized or "lich" in normalized)


def _find_patient_for_doctor(db: Session, doctor_id: int, reference: str) -> Optional[User]:
    if not reference:
        return None

    normalized_ref = _normalize_text(reference)
    patients = (
        db.query(User)
        .filter(User.role == UserRole.patient, User.doctor_id == doctor_id)
        .all()
    )

    for p in patients:
        full_name = _normalize_text(p.full_name or "")
        username = _normalize_text(p.username or "")
        if normalized_ref == full_name or normalized_ref == username:
            return p

    for p in patients:
        full_name = _normalize_text(p.full_name or "")
        username = _normalize_text(p.username or "")
        if normalized_ref in full_name or normalized_ref in username:
            return p

    return None


def _try_create_schedule_from_message(
    db: Session,
    doctor_id: int,
    user_message: str,
) -> Optional[Dict[str, Any]]:
    if not _is_schedule_command(user_message):
        return None

    exercise_name = _resolve_exercise_name(user_message)
    if not exercise_name:
        return {
            "reply": (
                "I detected a scheduling request, but I could not identify the exercise type. "
                "Please use one of: arm_raise, squat, calf_raise, single_leg_stand."
            ),
            "used_llm": False,
        }

    patient_ref = _extract_patient_reference(user_message)
    if not patient_ref:
        return {
            "reply": "I detected a scheduling request, but I could not identify the patient name after 'for/cho'.",
            "used_llm": False,
        }

    patient = _find_patient_for_doctor(db, doctor_id, patient_ref)
    if not patient:
        return {
            "reply": (
                f"I could not find patient '{patient_ref}' in your panel. "
                "Please use the exact patient full name shown in your patient context list."
            ),
            "used_llm": False,
        }

    scheduled_for = _resolve_scheduled_for(user_message)

    existing = (
        db.query(PatientSchedule)
        .filter(
            PatientSchedule.doctor_id == doctor_id,
            PatientSchedule.patient_id == patient.id,
            PatientSchedule.exercise_name == exercise_name,
            PatientSchedule.scheduled_for == scheduled_for,
        )
        .first()
    )
    if existing:
        return {
            "reply": (
                f"A schedule already exists for {patient.full_name}: {exercise_name} on "
                f"{scheduled_for.strftime('%Y-%m-%d')}. I did not create a duplicate."
            ),
            "used_llm": False,
        }

    created = PatientSchedule(
        doctor_id=doctor_id,
        patient_id=patient.id,
        exercise_name=exercise_name,
        scheduled_for=scheduled_for,
        note="Created by Doctor Assistant command",
        is_read=0,
    )
    db.add(created)
    db.commit()
    db.refresh(created)

    return {
        "reply": (
            f"Schedule created successfully for {patient.full_name}: {exercise_name} on "
            f"{scheduled_for.strftime('%Y-%m-%d')}. The patient will see this when they log in."
        ),
        "used_llm": False,
    }


def _serialize_sessions(items: List[DBSession]) -> List[Dict[str, Any]]:
    return [
        {
            "exercise_name": s.exercise_name,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "total_reps": int(s.total_reps or 0),
            "correct_reps": int(s.correct_reps or 0),
            "accuracy": round(float(s.accuracy or 0.0), 2),
            "duration_seconds": int(s.duration_seconds or 0),
        }
        for s in items
    ]


def _build_doctor_context(db: Session, doctor_id: int, patient_id: Optional[int]) -> Dict[str, Any]:
    doctor = db.query(User).filter(User.id == doctor_id, User.role == UserRole.doctor).first()
    if not doctor:
        return {}

    patients = (
        db.query(User)
        .filter(User.role == UserRole.patient, User.doctor_id == doctor_id)
        .order_by(User.full_name.asc())
        .all()
    )

    patient_ids = [p.id for p in patients]
    total_patients = len(patient_ids)

    context: Dict[str, Any] = {
        "doctor_profile": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "username": doctor.username,
        },
        "practice_summary": {
            "total_patients": total_patients,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }

    if not patient_ids:
        context["patient_summary_list"] = []
        return context

    sessions_per_patient = dict(
        db.query(DBSession.patient_id, func.count(DBSession.id))
        .filter(DBSession.patient_id.in_(patient_ids))
        .group_by(DBSession.patient_id)
        .all()
    )

    avg_accuracy_per_patient = dict(
        db.query(DBSession.patient_id, func.avg(DBSession.accuracy))
        .filter(DBSession.patient_id.in_(patient_ids))
        .group_by(DBSession.patient_id)
        .all()
    )

    last_session_per_patient: Dict[int, Optional[DBSession]] = {}
    for pid in patient_ids:
        last_session_per_patient[pid] = (
            db.query(DBSession)
            .filter(DBSession.patient_id == pid)
            .order_by(DBSession.start_time.desc())
            .first()
        )

    patient_summary_list: List[Dict[str, Any]] = []
    for p in patients:
        last = last_session_per_patient.get(p.id)
        patient_summary_list.append(
            {
                "patient_id": p.id,
                "full_name": p.full_name,
                "age": p.age,
                "mobility_level": p.mobility_level.value if p.mobility_level else None,
                "pain_level": p.pain_level,
                "session_count": int(sessions_per_patient.get(p.id, 0) or 0),
                "avg_accuracy": round(float(avg_accuracy_per_patient.get(p.id, 0.0) or 0.0), 2),
                "last_session": {
                    "exercise_name": last.exercise_name,
                    "start_time": last.start_time.isoformat() if last and last.start_time else None,
                    "accuracy": round(float(last.accuracy or 0.0), 2) if last else None,
                }
                if last
                else None,
            }
        )

    context["patient_summary_list"] = patient_summary_list[:20]

    if patient_id is not None:
        selected = next((p for p in patients if p.id == patient_id), None)
        if selected:
            recent_sessions = (
                db.query(DBSession)
                .filter(DBSession.patient_id == selected.id)
                .order_by(DBSession.start_time.desc())
                .limit(10)
                .all()
            )

            recurring_errors = (
                db.query(SessionError.error_name, func.sum(SessionError.count).label("count"))
                .join(DBSession, DBSession.id == SessionError.session_id)
                .filter(DBSession.patient_id == selected.id)
                .group_by(SessionError.error_name)
                .order_by(func.sum(SessionError.count).desc())
                .limit(5)
                .all()
            )

            context["selected_patient"] = {
                "patient_id": selected.id,
                "full_name": selected.full_name,
                "age": selected.age,
                "gender": selected.gender.value if selected.gender else None,
                "mobility_level": selected.mobility_level.value if selected.mobility_level else None,
                "pain_level": selected.pain_level,
                "medical_conditions": selected.medical_conditions,
                "injury_type": selected.injury_type,
                "recent_sessions": _serialize_sessions(recent_sessions),
                "recurring_errors": [{"name": n, "count": int(c)} for n, c in recurring_errors],
            }

    return context


def generate_doctor_assistant_reply(
    db: Session,
    doctor_id: int,
    user_message: str,
    patient_id: Optional[int] = None,
) -> Dict[str, Any]:
    command_result = _try_create_schedule_from_message(db, doctor_id, user_message)
    if command_result is not None:
        return command_result

    context = _build_doctor_context(db, doctor_id, patient_id)

    system_prompt = (
        "You are a Doctor Assistant for rehabilitation clinicians. "
        "Help with concise, practical, non-diagnostic coaching and care-planning insights. "
        "When discussing patient data, use only provided context. "
        "Prefer concise bullets for plans and concise paragraph for direct explanations. "
        "Never provide medication prescriptions or definitive diagnosis. "
        "If severe symptom patterns are discussed, recommend urgent clinical evaluation."
    )

    user_payload = {
        "doctor_message": user_message,
        "context": context,
        "response_format": {
            "style": "clinical_concise",
            "must_include": [
                "one key insight",
                "one suggested next action",
                "one safety/risk note if relevant",
            ],
        },
    }

    reply = _call_chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ]
    )

    return {
        "reply": reply,
        "used_llm": True,
    }
