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
            # Emotion tracking
            "emotion_history": [],
            "pain_incidents": 0,
            "fatigue_incidents": 0,
            "total_pain_level": 0.0,
            "total_fatigue_level": 0.0,
            "emotion_frame_count": 0,
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


def update_live_session_emotion(session_id: int, emotion_data: Dict[str, Any]) -> None:
    """Update emotion data for live session"""
    if not emotion_data:
        return

    with _lock:
        if session_id not in _live_session_stats:
            return

        stats = _live_session_stats[session_id]

        # Add to emotion history (keep last 50 entries to prevent memory bloat)
        stats["emotion_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "emotion": emotion_data["emotion"],
            "confidence": emotion_data["confidence"],
            "pain_level": emotion_data["pain_level"],
            "fatigue_level": emotion_data["fatigue_level"]
        })

        if len(stats["emotion_history"]) > 50:
            stats["emotion_history"].pop(0)

        # Update emotion counters
        stats["emotion_frame_count"] += 1
        stats["total_pain_level"] += emotion_data["pain_level"]
        stats["total_fatigue_level"] += emotion_data["fatigue_level"]

        # Count incidents (pain/fatigue levels above threshold)
        if emotion_data["pain_level"] > 0.6:
            stats["pain_incidents"] += 1
        if emotion_data["fatigue_level"] > 0.7:
            stats["fatigue_incidents"] += 1


def get_emotion_summary(session_id: int) -> Dict[str, Any]:
    """Get emotion summary for session"""
    with _lock:
        stats = _live_session_stats.get(session_id)
        if not stats or stats["emotion_frame_count"] == 0:
            return {}

        # Calculate averages
        avg_pain = stats["total_pain_level"] / stats["emotion_frame_count"]
        avg_fatigue = stats["total_fatigue_level"] / stats["emotion_frame_count"]

        # Find predominant emotion
        emotion_counts = {}
        for entry in stats["emotion_history"]:
            emotion = entry["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        predominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"

        return {
            "avg_pain_level": round(avg_pain, 3),
            "avg_fatigue_level": round(avg_fatigue, 3),
            "predominant_emotion": predominant_emotion,
            "pain_incidents": stats["pain_incidents"],
            "fatigue_incidents": stats["fatigue_incidents"],
            "emotion_frame_count": stats["emotion_frame_count"]
        }


def pop_live_session(session_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        stats = _live_session_stats.pop(session_id, None)
        return dict(stats) if stats else None
