"""Rule-based progression suggestion engine.

After each session ends, call check_and_create_suggestion().
If the patient achieved >= 80% accuracy over the last 3 sessions of the
same exercise, a ProgressionSuggestion record is created for the doctor.
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models import DBSession, User, UserExerciseLimits, ProgressionSuggestion

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSIONS_REQUIRED = 3       # consecutive qualifying sessions
_ACCURACY_THRESHOLD = 80.0   # percent
_COOLDOWN_DAYS = 7           # days before a new suggestion for the same exercise

# How much to increase each field when progressing.
# Keys must match UserExerciseLimits column names.
_DELTA: dict = {
    "squat": {
        "max_reps_per_set": 2,
        "difficulty_score": 0.1,
        "recommended_rest_seconds": -15,
    },
    "arm_raise": {
        "max_reps_per_set": 2,
        "difficulty_score": 0.1,
        "recommended_rest_seconds": -10,
    },
    "calf_raise": {
        "max_reps_per_set": 3,
        "difficulty_score": 0.1,
        "recommended_rest_seconds": -10,
    },
    "single_leg_stand": {
        "max_reps_per_set": 1,
        "difficulty_score": 0.15,
        "recommended_rest_seconds": -20,
    },
}

# Absolute floors so suggestions never go below safe minimums
_FLOOR_REST = 20      # seconds
_FLOOR_REPS = 3
_CEIL_DIFFICULTY = 1.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_and_create_suggestion(
    db: Session,
    patient_id: int,
    exercise_name: str,
) -> Optional[int]:
    """Check whether a progression suggestion should be created.

    Returns the new ProgressionSuggestion.id if one was created, else None.
    Called in a background task after every session.end endpoint.
    """
    delta = _DELTA.get(exercise_name)
    if delta is None:
        return None  # custom exercises — skip

    # --- fetch last N valid sessions for this exercise ---
    recent = (
        db.query(DBSession)
        .filter(
            DBSession.patient_id == patient_id,
            DBSession.exercise_name == exercise_name,
            DBSession.total_reps > 0,
            DBSession.accuracy.isnot(None),
        )
        .order_by(DBSession.start_time.desc())
        .limit(_SESSIONS_REQUIRED)
        .all()
    )

    if len(recent) < _SESSIONS_REQUIRED:
        return None

    accuracies = [float(s.accuracy or 0) for s in recent]
    if any(a < _ACCURACY_THRESHOLD for a in accuracies):
        return None

    avg_acc = round(sum(accuracies) / len(accuracies), 2)

    # --- cooldown: block only if there's an unreviewed (pending) suggestion ---
    # Approved suggestions do not block future progression — the patient may
    # qualify again after training at the new level for another 3 sessions.
    pending = (
        db.query(ProgressionSuggestion)
        .filter(
            ProgressionSuggestion.patient_id == patient_id,
            ProgressionSuggestion.exercise_name == exercise_name,
            ProgressionSuggestion.status == "pending",
        )
        .first()
    )
    if pending:
        return None

    # --- find patient's doctor ---
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient or not patient.doctor_id:
        return None

    # --- current limits snapshot ---
    limits = (
        db.query(UserExerciseLimits)
        .filter(
            UserExerciseLimits.user_id == patient_id,
            UserExerciseLimits.exercise_type == exercise_name,
        )
        .first()
    )

    current_reps = int(limits.max_reps_per_set) if limits and limits.max_reps_per_set else None
    current_diff = float(limits.difficulty_score) if limits and limits.difficulty_score else None
    current_rest = int(limits.recommended_rest_seconds) if limits and limits.recommended_rest_seconds else None

    # --- compute suggestions ---
    suggested_reps = _apply_delta_reps(current_reps, delta["max_reps_per_set"])
    suggested_diff = _apply_delta_diff(current_diff, delta["difficulty_score"])
    suggested_rest = _apply_delta_rest(current_rest, delta["recommended_rest_seconds"])

    suggestion = ProgressionSuggestion(
        patient_id=patient_id,
        doctor_id=patient.doctor_id,
        exercise_name=exercise_name,
        trigger_session_count=_SESSIONS_REQUIRED,
        avg_accuracy=avg_acc,
        trigger_session_ids=json.dumps([s.id for s in recent]),
        current_reps=current_reps,
        current_difficulty=current_diff,
        current_rest_seconds=current_rest,
        suggested_reps=suggested_reps,
        suggested_difficulty=suggested_diff,
        suggested_rest_seconds=suggested_rest,
        status="pending",
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion.id


def apply_suggestion(
    db: Session,
    suggestion: ProgressionSuggestion,
    doctor_note: Optional[str] = None,
) -> None:
    """Apply an approved suggestion to UserExerciseLimits and mark it approved."""
    limits = (
        db.query(UserExerciseLimits)
        .filter(
            UserExerciseLimits.user_id == suggestion.patient_id,
            UserExerciseLimits.exercise_type == suggestion.exercise_name,
        )
        .first()
    )

    now = datetime.utcnow()

    if limits is None:
        limits = UserExerciseLimits(
            user_id=suggestion.patient_id,
            exercise_type=suggestion.exercise_name,
            created_at=now,
        )
        db.add(limits)

    if suggestion.suggested_reps is not None:
        limits.max_reps_per_set = suggestion.suggested_reps
    if suggestion.suggested_difficulty is not None:
        limits.difficulty_score = min(suggestion.suggested_difficulty, _CEIL_DIFFICULTY)
    if suggestion.suggested_rest_seconds is not None:
        limits.recommended_rest_seconds = max(suggestion.suggested_rest_seconds, _FLOOR_REST)
    limits.updated_at = now

    suggestion.status = "approved"
    suggestion.doctor_note = doctor_note
    suggestion.updated_at = now

    db.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_delta_reps(current: Optional[int], delta: int) -> int:
    base = current if current is not None else 10
    return max(_FLOOR_REPS, base + delta)


def _apply_delta_diff(current: Optional[float], delta: float) -> float:
    base = current if current is not None else 0.5
    return round(min(_CEIL_DIFFICULTY, base + delta), 2)


def _apply_delta_rest(current: Optional[int], delta: int) -> int:
    base = current if current is not None else 60
    return max(_FLOOR_REST, base + delta)
