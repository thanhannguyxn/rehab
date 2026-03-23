"""Patient coach agent service with safety guardrails and LLM completion."""

import json
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User, DBSession, SessionError, UserExerciseLimits
from settings import LLM_API_BASE_URL, LLM_API_KEY, LLM_MODEL

_RED_FLAG_KEYWORDS = [
    "chest pain",
    "dizzy",
    "dizziness",
    "faint",
    "shortness of breath",
    "fall",
    "severe pain",
    "numbness",
    "mat y thuc",
    "ngat",
    "dau nguc",
    "chong mat",
    "kho tho",
    "te bi",
    "nga",
    "kho tho dot ngot",
    "dau nguc du doi",
    "te tay chan",
    "bat tinh",
]

_MODERATE_PAIN_KEYWORDS = [
    "persistent pain",
    "pain for hours",
    "pain not going away",
    "swelling",
    "joint swelling",
    "cannot continue",
    "cant continue",
    "worsening pain",
    "increased pain",
    "moderate pain",
    "dau keo dai",
    "dau tang dan",
    "sung khop",
    "dau lien tuc",
    "dau khong giam",
    "khong tap tiep duoc",
    "dau vai gio",
    "khop bi sung",
]

_MILD_DISCOMFORT_KEYWORDS = [
    "mild pain",
    "slight pain",
    "slight discomfort",
    "a little pain",
    "sore",
    "soreness",
    "stiff",
    "stiffness",
    "uncomfortable",
    "minor discomfort",
    "mild discomfort",
    "hoi dau",
    "hoi cang",
    "kho chiu nhe",
    "hoi moi",
    "nhuc nhe",
    "cang co nhe",
    "dau nhe",
]

_PROFILE_CONSENT_PHRASES = [
    "yes show my profile",
    "yes, show my profile",
    "i consent to show my profile",
    "you can show my profile",
    "toi dong y cho xem ho so",
    "vâng cho xem hồ sơ",
    "vang cho xem ho so",
]

_PROFILE_DATA_REQUEST_KEYWORDS = [
    "my profile",
    "personal information",
    "personal info",
    "my information",
    "extract my personal",
    "profile summary",
    "show my profile",
    "thong tin ca nhan",
    "ho so cua toi",
]


_VIETNAMESE_HINT_WORDS = [
    "toi",
    "ban",
    "khong",
    "dau",
    "tap",
    "khop",
    "choang",
    "mat",
    "nguc",
    "tho",
    "hom nay",
    "nhu the nao",
]


_SAFETY_MESSAGES = {
    "severe": {
        "en": (
            "I detected a potential safety risk. Stop exercising now, sit or lie down safely, "
            "and contact your doctor or local emergency services if symptoms are severe or continue."
        ),
        "vi": (
            "Tôi phát hiện dấu hiệu nguy cơ an toàn. Hãy dừng tập ngay, ngồi hoặc nằm ở vị trí an toàn, "
            "và liên hệ bác sĩ hoặc cấp cứu địa phương nếu triệu chứng nặng hoặc kéo dài."
        ),
    },
    "moderate": {
        "en": (
            "Your symptoms may be more than normal exercise discomfort. Stop this session now, "
            "rest, and contact your doctor if symptoms persist or worsen."
        ),
        "vi": (
            "Triệu chứng của bạn có thể vượt quá mức khó chịu thông thường khi tập. "
            "Hãy dừng buổi tập này, nghỉ ngơi, và liên hệ bác sĩ nếu triệu chứng kéo dài hoặc nặng hơn."
        ),
    },
    "mild": {
        "en": (
            "This sounds like mild discomfort. Slow down, reduce range of motion, lower reps, "
            "and keep movements controlled. Stop if symptoms increase."
        ),
        "vi": (
            "Đây có vẻ là khó chịu nhẹ. Hãy giảm tốc độ, giảm biên độ vận động, giảm số lần lặp, "
            "và giữ chuyển động có kiểm soát. Dừng lại nếu triệu chứng tăng lên."
        ),
    },
}


def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _normalize_for_match(text: str) -> str:
    """Normalize text for robust matching across accented/non-accented Vietnamese."""
    lowered = (text or "").lower().replace("đ", "d")
    without_accents = "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )
    return " ".join(without_accents.split())


def _contains_any(normalized_text: str, keywords: List[str]) -> bool:
    return any(_normalize_for_match(keyword) in normalized_text for keyword in keywords)


def _is_vietnamese_message(user_message: str) -> bool:
    """Detect whether user likely wrote in Vietnamese (accented or unaccented)."""
    raw = user_message or ""
    if any(ch in raw for ch in "ăâđêôơưáàảãạéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵĂÂĐÊÔƠƯÁÀẢÃẠÉÈẺẼẸÍÌỈĨỊÓÒỎÕỌÚÙỦŨỤÝỲỶỸỴ"):
        return True

    normalized = _normalize_for_match(raw)
    return _contains_any(normalized, _VIETNAMESE_HINT_WORDS)


def _get_safety_message(level: str, is_vietnamese: bool) -> str:
    language = "vi" if is_vietnamese else "en"
    return _SAFETY_MESSAGES[level][language]


def _has_profile_consent(user_message: str) -> bool:
    normalized = _normalize_for_match(user_message)
    return _contains_any(normalized, _PROFILE_CONSENT_PHRASES)


def _requests_personal_profile(user_message: str) -> bool:
    normalized = _normalize_for_match(user_message)
    return _contains_any(normalized, _PROFILE_DATA_REQUEST_KEYWORDS)


def _check_safety_escalation(user_message: str) -> Tuple[bool, Optional[str]]:
    """Check if message contains red-flag keywords indicating safety risk."""
    normalized = _normalize_for_match(user_message)
    if _contains_any(normalized, _RED_FLAG_KEYWORDS):
        is_vietnamese = _is_vietnamese_message(user_message)
        return (
            True,
            _get_safety_message("severe", is_vietnamese),
        )
    return False, None


def _assess_safety_level(user_message: str) -> Tuple[str, Optional[str], bool]:
    """Assess safety severity and return (level, message, should_skip_llm)."""
    is_vietnamese = _is_vietnamese_message(user_message)

    severe, severe_message = _check_safety_escalation(user_message)
    if severe:
        return "severe", severe_message, True

    normalized = _normalize_for_match(user_message)

    if _contains_any(normalized, _MODERATE_PAIN_KEYWORDS):
        return (
            "moderate",
            _get_safety_message("moderate", is_vietnamese),
            True,
        )

    if _contains_any(normalized, _MILD_DISCOMFORT_KEYWORDS):
        return (
            "mild",
            _get_safety_message("mild", is_vietnamese),
            True,
        )

    return "none", None, False


def _detect_response_style(user_message: str) -> str:
    """Map question intent to a response style."""
    normalized = _normalize_for_match(user_message)

    if any(phrase in normalized for phrase in ["how to", "how do i", "how can i", "how should i", "cach", "nhu the nao"]):
        return "steps"

    if any(phrase in normalized for phrase in ["why", "tai sao", "vi sao"]):
        return "paragraph"

    if any(phrase in normalized for phrase in ["summary", "summarize", "recap", "overview", "tong ket", "tom tat"]):
        return "bullets"

    return "adaptive"


def _serialize_recent_sessions(sessions: List[DBSession]) -> List[Dict[str, Any]]:
    """Serialize session data for LLM context."""
    serialized: List[Dict[str, Any]] = []
    for item in sessions:
        serialized.append(
            {
                "exercise_name": item.exercise_name,
                "start_time": item.start_time.isoformat() if item.start_time else None,
                "total_reps": item.total_reps or 0,
                "correct_reps": item.correct_reps or 0,
                "accuracy": round(float(item.accuracy or 0.0), 2),
                "duration_seconds": int(item.duration_seconds or 0),
            }
        )
    return serialized


def _build_patient_context(db: Session, user_id: int, exercise_type: Optional[str]) -> Dict[str, Any]:
    """Build comprehensive context from patient profile, sessions, and exercise history."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}

    recent_sessions = (
        db.query(DBSession)
        .filter(DBSession.patient_id == user_id)
        .order_by(DBSession.start_time.desc())
        .limit(10)
        .all()
    )

    avg_accuracy = (
        db.query(func.avg(DBSession.accuracy))
        .filter(DBSession.patient_id == user_id)
        .scalar()
    )

    all_sessions = (
        db.query(DBSession)
        .filter(DBSession.patient_id == user_id)
        .order_by(DBSession.start_time.asc())
        .all()
    )
    accuracy_trend = None
    if len(all_sessions) >= 2:
        old_n = min(5, len(all_sessions))
        new_n = min(5, len(all_sessions))
        old_avg = sum(s.accuracy or 0.0 for s in all_sessions[:old_n]) / old_n
        new_avg = sum(s.accuracy or 0.0 for s in all_sessions[-new_n:]) / new_n
        accuracy_trend = round(float(new_avg - old_avg), 2)

    unique_exercises = (
        db.query(DBSession.exercise_name)
        .filter(DBSession.patient_id == user_id)
        .distinct()
        .all()
    )

    total_sessions_count = (
        db.query(func.count(DBSession.id))
        .filter(DBSession.patient_id == user_id)
        .scalar()
    ) or 0

    recurring_errors = (
        db.query(SessionError.error_name, func.sum(SessionError.count).label("count"))
        .join(DBSession, DBSession.id == SessionError.session_id)
        .filter(DBSession.patient_id == user_id)
        .group_by(SessionError.error_name)
        .order_by(func.sum(SessionError.count).desc())
        .limit(5)
        .all()
    )

    saved_limit = None
    if exercise_type:
        saved_limit = (
            db.query(UserExerciseLimits)
            .filter(
                UserExerciseLimits.user_id == user_id,
                UserExerciseLimits.exercise_type == exercise_type,
            )
            .first()
        )

    return {
        "profile": {
            "full_name": user.full_name,
            "age": user.age,
            "gender": user.gender.value if user.gender else None,
            "mobility_level": user.mobility_level.value if user.mobility_level else None,
            "pain_level": user.pain_level,
            "bmi": float(user.bmi) if user.bmi is not None else None,
            "medical_conditions": user.medical_conditions,
            "injury_type": user.injury_type,
        },
        "exercise_focus": exercise_type,
        "recent_sessions": _serialize_recent_sessions(recent_sessions),
        "progress_summary": {
            "total_sessions": int(total_sessions_count),
            "unique_exercises": [ex[0] for ex in unique_exercises] if unique_exercises else [],
            "avg_accuracy": round(float(avg_accuracy or 0.0), 2),
            "accuracy_trend": accuracy_trend,
        },
        "avg_accuracy": round(float(avg_accuracy or 0.0), 2),
        "recurring_errors": [{"name": name, "count": int(count)} for name, count in recurring_errors],
        "saved_limits": {
            "max_depth_angle": saved_limit.max_depth_angle if saved_limit else None,
            "min_raise_angle": saved_limit.min_raise_angle if saved_limit else None,
            "max_reps_per_set": saved_limit.max_reps_per_set if saved_limit else None,
            "recommended_rest_seconds": saved_limit.recommended_rest_seconds if saved_limit else None,
            "difficulty_score": saved_limit.difficulty_score if saved_limit else None,
            "injury_risk_score": saved_limit.injury_risk_score if saved_limit else None,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


def _call_chat_completion(messages: List[Dict[str, str]]) -> str:
    """Call LLM API with fallback if key missing or request fails."""
    if not LLM_API_KEY:
        return (
            "Patient Coach is configured but LLM_API_KEY is missing. Please set it in backend/.env. "
            "For now: keep today light, focus on form, and stop if pain increases."
        )

    endpoint = LLM_API_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "temperature": 0.4,
        "max_tokens": 800,
        "messages": messages,
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with request.urlopen(req, timeout=25) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                return data["choices"][0]["message"]["content"].strip()
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            if exc.code == 401:
                return (
                    "The LLM API key is invalid or expired. Please update LLM_API_KEY in backend/.env "
                    "and restart the backend."
                )

            if exc.code == 403:
                return (
                    "The LLM provider rejected access (403 Forbidden). Check key permissions, model access, "
                    "or provider region/account restrictions, then retry."
                )

            if exc.code == 429:
                retry_after_raw = exc.headers.get("Retry-After") if getattr(exc, "headers", None) else None
                if attempt == 0:
                    wait_seconds = 2
                    if retry_after_raw and retry_after_raw.isdigit():
                        wait_seconds = max(1, min(int(retry_after_raw), 10))
                    time.sleep(wait_seconds)
                    continue

                if (
                    "insufficient_quota" in body
                    or "exceeded your current quota" in body.lower()
                    or "rate limit" in body.lower()
                ):
                    return (
                        "The LLM account hit quota or rate limits. Wait 10-30 seconds and retry, "
                        "or switch to another key/provider."
                    )

            return (
                "The LLM service returned an error. Keep the session gentle today, focus on controlled reps, "
                "and stop if pain rises."
            )
        except (error.URLError, KeyError, IndexError, json.JSONDecodeError):
            return (
                "I could not reach the LLM service right now. Keep the session gentle today, "
                "focus on slow controlled reps, and stop if pain rises."
            )


def generate_patient_coach_reply(
    db: Session,
    user_id: int,
    user_message: str,
    exercise_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Main entry point: generate patient coach reply with safety checks and LLM."""
    profile_consent = _has_profile_consent(user_message)
    response_style = _detect_response_style(user_message)

    safety_level, safety_message, skip_llm = _assess_safety_level(user_message)
    if skip_llm:
        return {
            "reply": safety_message or "Please pause and prioritize safety.",
            "safety_escalation": safety_level in {"moderate", "severe"},
            "used_llm": False,
        }

    if _requests_personal_profile(user_message) and not profile_consent:
        return {
            "reply": (
                "I can help with your exercise safely, but I will keep personal profile details private by default. "
                "If you want your full profile summary, reply exactly: yes show my profile"
            ),
            "safety_escalation": False,
            "used_llm": False,
        }

    context = _build_patient_context(db, user_id, exercise_type)

    system_prompt = (
        "You are a rehabilitation Patient Coach Agent specializing in personalized exercise guidance. "
        "You have access to the patient's complete exercise history and progress data. "
        "COMMUNICATION STYLE: use simple language and follow this mapping exactly: "
        "if user asks 'how to' style questions, reply as numbered steps; "
        "if user asks 'why', reply as a short paragraph explanation; "
        "if user asks for summary/recap, reply as concise bullet points; "
        "otherwise choose the clearest concise format. "
        "PRIVACY RULE: do not reveal detailed profile fields (full_name, age, gender, bmi, medical_conditions, "
        "injury_type) unless the user explicitly consents with the phrase 'yes show my profile' in the current "
        "message. Without consent, keep profile details minimal and non-identifying. "
        "SAFETY LADDER: mild discomfort => suggest modify/slow down; "
        "moderate persistent pain => stop session and suggest doctor contact; "
        "severe red flags => emergency advice immediately. "
        "When asked about progress or history, summarize total sessions, unique exercises, avg accuracy, trend, "
        "and recurring errors from context. "
        "Do not diagnose diseases or prescribe medication. "
        "If user reports severe symptoms, instruct immediate stop and seek medical care."
    )

    user_payload = {
        "user_message": user_message,
        "profile_sharing_consent": profile_consent,
        "response_style_request": response_style,
        "context": context,
        "response_format": {
            "style": "short_supportive",
            "must_include": [
                "one clear next action or insight",
                "one form reminder",
                "one safety reminder",
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
        "safety_escalation": False,
        "used_llm": True,
    }
