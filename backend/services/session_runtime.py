from datetime import datetime
from threading import Lock
from typing import Any, Dict, Optional

# In-memory live stats keyed by session_id.
_live_session_stats: Dict[int, Dict[str, Any]] = {}
_lock = Lock()


def start_live_session(session_id: int) -> None:
    with _lock:
        _live_session_stats[session_id] = {
            "total_reps": 0,
            "correct_reps": 0,
            "accuracy": 0.0,
            "error_counts": {},
            "last_update": datetime.utcnow(),
        }


def update_live_session(session_id: int, rep_counter: Any) -> None:
    total_reps = int(getattr(rep_counter, "rep_count", 0) or 0)
    all_rep_errors = list(getattr(rep_counter, "all_rep_errors", []) or [])

    correct_reps = sum(1 for rep_errors in all_rep_errors if len(rep_errors) == 0)
    correct_reps = min(correct_reps, total_reps)

    error_counts: Dict[str, int] = {}
    for rep_errors in all_rep_errors:
        for error_name in rep_errors:
            error_counts[error_name] = error_counts.get(error_name, 0) + 1

    accuracy = round((correct_reps / total_reps) * 100, 2) if total_reps > 0 else 0.0

    with _lock:
        _live_session_stats[session_id] = {
            "total_reps": total_reps,
            "correct_reps": correct_reps,
            "accuracy": accuracy,
            "error_counts": error_counts,
            "last_update": datetime.utcnow(),
        }


def get_live_session(session_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        stats = _live_session_stats.get(session_id)
        return dict(stats) if stats else None


def pop_live_session(session_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        stats = _live_session_stats.pop(session_id, None)
        return dict(stats) if stats else None
