"""Tool definitions and execution for the Doctor Assistant agent."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models import User, UserRole, PatientSchedule


# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "create_patient_schedule",
            "description": "Create an exercise schedule for a patient. Call this when the doctor explicitly wants to schedule or assign an exercise to a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The numeric ID of the patient (required)."
                    },
                    "exercise_name": {
                        "type": "string",
                        "description": "Exercise name. Must be one of: arm_raise, squat, calf_raise, single_leg_stand.",
                        "enum": ["arm_raise", "squat", "calf_raise", "single_leg_stand"]
                    },
                    "scheduled_for": {
                        "type": "string",
                        "description": "ISO 8601 datetime string for when to schedule the exercise, e.g. '2026-03-27T09:00:00'."
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note for the patient."
                    }
                },
                "required": ["patient_id", "exercise_name", "scheduled_for"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_doctor_patients",
            "description": "List all patients assigned to the authenticated doctor. Returns patient IDs, names, and basic summary stats.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_details",
            "description": "Retrieve detailed information about a specific patient, including demographics, recent sessions, and recurring form errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The numeric ID of the patient."
                    }
                },
                "required": ["patient_id"]
            }
        }
    },
]

TOOL_NAMES = {d["function"]["name"] for d in TOOL_DEFINITIONS}


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_list_patients(db: Session, doctor_id: int) -> Dict[str, Any]:
    """Implement the list_doctor_patients tool."""
    patients = (
        db.query(User)
        .filter(User.role == UserRole.patient, User.doctor_id == doctor_id)
        .order_by(User.full_name.asc())
        .limit(20)
        .all()
    )

    if not patients:
        return {
            "status": "success",
            "count": 0,
            "patients": [],
            "message": "You have no patients assigned."
        }

    patient_summaries = []
    for p in patients:
        patient_summaries.append({
            "patient_id": p.id,
            "full_name": p.full_name,
            "age": p.age,
            "mobility_level": p.mobility_level.value if p.mobility_level else None,
            "pain_level": p.pain_level,
        })

    return {
        "status": "success",
        "count": len(patient_summaries),
        "patients": patient_summaries,
        "message": f"You have {len(patient_summaries)} patient(s) assigned."
    }


def _tool_get_patient_details(db: Session, doctor_id: int, patient_id: int) -> Dict[str, Any]:
    """Implement the get_patient_details tool."""
    patient = (
        db.query(User)
        .filter(User.id == patient_id, User.role == UserRole.patient, User.doctor_id == doctor_id)
        .first()
    )

    if not patient:
        return {
            "status": "error",
            "message": f"Patient with ID {patient_id} not found or not assigned to you."
        }

    from models import DBSession, SessionError
    from sqlalchemy import func

    recent_sessions = (
        db.query(DBSession)
        .filter(DBSession.patient_id == patient_id)
        .order_by(DBSession.start_time.desc())
        .limit(10)
        .all()
    )

    recurring_errors = (
        db.query(SessionError.error_name, func.sum(SessionError.count).label("count"))
        .join(DBSession, DBSession.id == SessionError.session_id)
        .filter(DBSession.patient_id == patient_id)
        .group_by(SessionError.error_name)
        .order_by(func.sum(SessionError.count).desc())
        .limit(5)
        .all()
    )

    sessions_data = [
        {
            "exercise_name": s.exercise_name,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "total_reps": int(s.total_reps or 0),
            "correct_reps": int(s.correct_reps or 0),
            "accuracy": round(float(s.accuracy or 0.0), 2),
            "duration_seconds": int(s.duration_seconds or 0),
        }
        for s in recent_sessions
    ]

    return {
        "status": "success",
        "patient": {
            "patient_id": patient.id,
            "full_name": patient.full_name,
            "age": patient.age,
            "gender": patient.gender.value if patient.gender else None,
            "mobility_level": patient.mobility_level.value if patient.mobility_level else None,
            "pain_level": patient.pain_level,
            "medical_conditions": patient.medical_conditions,
            "injury_type": patient.injury_type,
            "recent_sessions": sessions_data,
            "recurring_errors": [{"name": name, "count": int(count)} for name, count in recurring_errors],
        }
    }


def _tool_create_schedule(
    db: Session,
    doctor_id: int,
    patient_id: int,
    exercise_name: str,
    scheduled_for: str,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Implement the create_patient_schedule tool."""
    if exercise_name not in ("arm_raise", "squat", "calf_raise", "single_leg_stand"):
        return {
            "status": "error",
            "message": (
                f"Invalid exercise '{exercise_name}'. "
                "Supported exercises: arm_raise, squat, calf_raise, single_leg_stand."
            )
        }

    patient = (
        db.query(User)
        .filter(User.id == patient_id, User.role == UserRole.patient, User.doctor_id == doctor_id)
        .first()
    )
    if not patient:
        return {
            "status": "error",
            "message": f"Patient with ID {patient_id} not found or not assigned to you."
        }

    try:
        scheduled_dt = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {
            "status": "error",
            "message": f"Invalid date format '{scheduled_for}'. Use ISO 8601 format, e.g. '2026-03-27T09:00:00'."
        }

    existing = (
        db.query(PatientSchedule)
        .filter(
            PatientSchedule.doctor_id == doctor_id,
            PatientSchedule.patient_id == patient_id,
            PatientSchedule.exercise_name == exercise_name,
            PatientSchedule.scheduled_for == scheduled_dt,
        )
        .first()
    )
    if existing:
        return {
            "status": "duplicate",
            "message": (
                f"A schedule already exists for {patient.full_name}: {exercise_name} on "
                f"{scheduled_dt.strftime('%Y-%m-%d')}. No duplicate was created."
            )
        }

    schedule = PatientSchedule(
        doctor_id=doctor_id,
        patient_id=patient_id,
        exercise_name=exercise_name,
        scheduled_for=scheduled_dt,
        note=note or "Created by Doctor Assistant",
        is_read=0,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {
        "status": "success",
        "message": (
            f"Schedule created for {patient.full_name}: {exercise_name} on "
            f"{scheduled_dt.strftime('%Y-%m-%d')}. The patient will see this when they log in."
        ),
        "schedule_id": schedule.id,
    }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def execute_tool(
    db: Session,
    doctor_id: int,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch a tool call to the appropriate implementation."""
    if tool_name == "list_doctor_patients":
        return _tool_list_patients(db, doctor_id)
    elif tool_name == "get_patient_details":
        return _tool_get_patient_details(db, doctor_id, **arguments)
    elif tool_name == "create_patient_schedule":
        return _tool_create_schedule(db, doctor_id, **arguments)
    else:
        return {
            "status": "error",
            "message": f"Unknown tool '{tool_name}'."
        }


def build_tool_result_message(tool_result: Dict[str, Any]) -> str:
    """Format a tool result dict into a readable string for the LLM."""
    lines = []
    status = tool_result.get("status", "unknown")
    message = tool_result.get("message")

    if message:
        lines.append(message)

    if status == "success" and "count" in tool_result:
        patients = tool_result.get("patients", [])
        if patients:
            lines.append("")
            lines.append("Patients:")
            for p in patients:
                lines.append(
                    f"  - [{p['patient_id']}] {p['full_name']} "
                    f"(age {p.get('age', '?')}, mobility: {p.get('mobility_level', '?')})"
                )

    if status == "success" and "patient" in tool_result:
        pt = tool_result["patient"]
        lines.append("")
        lines.append(f"Patient: {pt['full_name']}")
        lines.append(f"  Age: {pt.get('age', '?')} | Gender: {pt.get('gender', '?')}")
        lines.append(f"  Mobility: {pt.get('mobility_level', '?')} | Pain: {pt.get('pain_level', '?')}")
        lines.append(f"  Injury: {pt.get('injury_type') or 'N/A'}")

        if pt.get("recent_sessions"):
            lines.append("  Recent sessions:")
            for s in pt["recent_sessions"][:5]:
                lines.append(
                    f"    - {s['exercise_name']} | accuracy: {s['accuracy']}% | "
                    f"reps: {s['correct_reps']}/{s['total_reps']}"
                )
        if pt.get("recurring_errors"):
            lines.append("  Recurring errors:")
            for e in pt["recurring_errors"]:
                lines.append(f"    - {e['name']} (x{e['count']})")

    return "\n".join(lines).strip()
