"""Patient coach agent service with conversation memory, safety guardrails, and LLM completion."""

import json
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User, DBSession, SessionError, UserExerciseLimits, ChatMessage, ConversationRole, PatientSchedule, ProgressionSuggestion
from settings import LLM_API_BASE_URL, LLM_API_KEY, LLM_MODEL

_AGENT_TYPE = "patient_coach"
_MAX_HISTORY_MESSAGES = 20  # keep last 20 exchanges (10 user + 10 assistant)

# ---------------------------------------------------------------------------
# Safety keyword lists (unchanged)
# ---------------------------------------------------------------------------

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
    # English
    "yes show my profile",
    "yes, show my profile",
    "i consent to show my profile",
    "you can show my profile",
    "show my profile",
    "allow profile",
    "i allow",
    "i agree",
    "yes please",
    # Vietnamese có dấu
    "vâng cho xem hồ sơ",
    "cho xem hồ sơ",
    "tôi cho phép",
    "tôi đồng ý",
    "được xem hồ sơ",
    "cho phép xem hồ sơ",
    "tôi cho phép xem hồ sơ",
    "tôi đồng ý cho xem hồ sơ",
    "đồng ý xem hồ sơ",
    "xem hồ sơ đi",
    "ok xem đi",
    "ừ cho xem",
    "vâng",
    "ok",
    "đồng ý",
    # Vietnamese không dấu
    "toi cho phep",
    "toi dong y",
    "vang cho xem ho so",
    "cho phep xem ho so",
    "toi cho phep xem ho so",
    "dong y xem ho so",
    "xem ho so di",
    "ok xem di",
    "u cho xem",
    "dong y",
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
    "toi", "ban", "khong", "dau", "tap", "khop",
    "choang", "mat", "nguc", "tho", "hom nay", "nhu the nao",
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

# ---------------------------------------------------------------------------
# Utility helpers (unchanged)
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _normalize_for_match(text: str) -> str:
    lowered = (text or "").lower().replace("đ", "d")
    without_accents = "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )
    return " ".join(without_accents.split())


def _contains_any(normalized_text: str, keywords: List[str]) -> bool:
    return any(_normalize_for_match(keyword) in normalized_text for keyword in keywords)


def _is_vietnamese_message(user_message: str) -> bool:
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
    normalized = _normalize_for_match(user_message)
    if _contains_any(normalized, _RED_FLAG_KEYWORDS):
        is_vietnamese = _is_vietnamese_message(user_message)
        return True, _get_safety_message("severe", is_vietnamese)
    return False, None


def _assess_safety_level(user_message: str) -> Tuple[str, Optional[str], bool]:
    is_vietnamese = _is_vietnamese_message(user_message)

    severe, severe_message = _check_safety_escalation(user_message)
    if severe:
        return "severe", severe_message, True

    normalized = _normalize_for_match(user_message)

    if _contains_any(normalized, _MODERATE_PAIN_KEYWORDS):
        return "moderate", _get_safety_message("moderate", is_vietnamese), True

    if _contains_any(normalized, _MILD_DISCOMFORT_KEYWORDS):
        return "mild", _get_safety_message("mild", is_vietnamese), True

    return "none", None, False


def _detect_response_style(user_message: str) -> str:
    normalized = _normalize_for_match(user_message)
    if any(phrase in normalized for phrase in ["how to", "how do i", "how can i", "how should i", "cach", "nhu the nao"]):
        return "steps"
    if any(phrase in normalized for phrase in ["why", "tai sao", "vi sao"]):
        return "paragraph"
    if any(phrase in normalized for phrase in ["summary", "summarize", "recap", "overview", "tong ket", "tom tat"]):
        return "bullets"
    return "adaptive"


def _serialize_recent_sessions(sessions: List[DBSession]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for item in sessions:
        serialized.append({
            "exercise_name": item.exercise_name,
            "start_time": item.start_time.isoformat() if item.start_time else None,
            "total_reps": item.total_reps or 0,
            "correct_reps": item.correct_reps or 0,
            "accuracy": round(float(item.accuracy or 0.0), 2),
            "duration_seconds": int(item.duration_seconds or 0),
        })
    return serialized


def _build_patient_context(db: Session, user_id: int, exercise_type: Optional[str]) -> Dict[str, Any]:
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

    recent_progressions = (
        db.query(ProgressionSuggestion)
        .filter(
            ProgressionSuggestion.patient_id == user_id,
            ProgressionSuggestion.status == "approved",
        )
        .order_by(ProgressionSuggestion.updated_at.desc())
        .limit(3)
        .all()
    )

    upcoming_schedules = (
        db.query(PatientSchedule)
        .filter(
            PatientSchedule.patient_id == user_id,
            PatientSchedule.scheduled_for >= datetime.utcnow(),
        )
        .order_by(PatientSchedule.scheduled_for.asc())
        .limit(5)
        .all()
    )

    past_schedules = (
        db.query(PatientSchedule)
        .filter(
            PatientSchedule.patient_id == user_id,
            PatientSchedule.scheduled_for < datetime.utcnow(),
        )
        .order_by(PatientSchedule.scheduled_for.desc())
        .limit(3)
        .all()
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
        "recent_progressions": [
            {
                "exercise_name": p.exercise_name,
                "prev_reps": p.current_reps,
                "new_reps": p.suggested_reps,
                "prev_difficulty": p.current_difficulty,
                "new_difficulty": p.suggested_difficulty,
                "approved_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in recent_progressions
        ],
        "upcoming_schedules": [
            {
                "exercise_name": s.exercise_name,
                "scheduled_for": s.scheduled_for.isoformat() if s.scheduled_for else None,
                "note": s.note,
            }
            for s in upcoming_schedules
        ],
        "past_schedules": [
            {
                "exercise_name": s.exercise_name,
                "scheduled_for": s.scheduled_for.isoformat() if s.scheduled_for else None,
                "note": s.note,
            }
            for s in past_schedules
        ],
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


def _load_conversation_history(db: Session, user_id: int) -> List[Dict[str, str]]:
    """Load the most recent conversation messages from DB for context."""
    rows = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == user_id,
            ChatMessage.agent_type == _AGENT_TYPE,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(_MAX_HISTORY_MESSAGES)
        .all()
    )
    # Return in chronological order (oldest first)
    return [
        {"role": row.role.value, "content": row.content}
        for row in reversed(rows)
    ]


def _save_message(
    db: Session,
    user_id: int,
    role: ConversationRole,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a chat message to the database."""
    msg = ChatMessage(
        user_id=user_id,
        agent_type=_AGENT_TYPE,
        role=role,
        content=content,
        metadata_=json.dumps(metadata) if metadata else None,
    )
    db.add(msg)
    db.commit()


def _call_chat_completion(messages: List[Dict[str, str]]) -> str:
    """Call OpenAI-compatible API (Groq). messages uses role/content dicts."""
    if not LLM_API_KEY:
        return (
            "Huấn luyện viên đã được cấu hình nhưng thiếu LLM_API_KEY. Vui lòng đặt giá trị trong backend/.env. "
            "Trong thời gian này: hãy tập nhẹ nhàng, tập trung vào tư thế, và dừng lại nếu cơn đau tăng lên."
        )

    endpoint = LLM_API_BASE_URL.rstrip("/") + "/chat/completions"
    payload: Dict[str, Any] = {
        "model": LLM_MODEL,
        "temperature": 0.5,
        "max_tokens": 1024,
        "messages": messages,
    }

    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
            "User-Agent": "Mozilla/5.0 (compatible; rehab-chatbot/1.0)",
        },
        method="POST",
    )

    for attempt in range(2):
        try:
            with request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                return data["choices"][0]["message"]["content"].strip()
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            try:
                err_msg = json.loads(body).get("error", {}).get("message", "")
            except Exception:
                err_msg = body[:200] if body else ""
            if exc.code in (401, 403):
                return f"API key không hợp lệ (HTTP {exc.code}): {err_msg}"
            if exc.code == 429:
                if attempt == 0:
                    time.sleep(2)
                    continue
                return f"Đã đạt giới hạn API: {err_msg or 'Rate limit.'}"
            return f"Lỗi API HTTP {exc.code}: {err_msg or body[:200]}"
        except (error.URLError, TimeoutError, OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"Không thể kết nối dịch vụ AI: {exc}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_patient_coach_reply(
    db: Session,
    user_id: int,
    user_message: str,
    exercise_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate patient coach reply with conversation memory, safety checks, and LLM.
    All user/assistant messages are persisted to the database.
    """
    safety_level, safety_message, skip_llm = _assess_safety_level(user_message)

    # Load conversation history BEFORE saving the new user message
    # (so it includes prior exchanges but not the current one yet)
    conversation_history = _load_conversation_history(db, user_id)

    # Save user message immediately so it persists even if the request fails
    _save_message(
        db,
        user_id=user_id,
        role=ConversationRole.user,
        content=user_message,
        metadata={"exercise_type": exercise_type},
    )

    if skip_llm:
        _save_message(
            db,
            user_id=user_id,
            role=ConversationRole.assistant,
            content=safety_message or "Vui lòng dừng lại và ưu tiên an toàn.",
            metadata={"safety_escalation": safety_level in {"moderate", "severe"}, "used_llm": False},
        )
        return {
            "reply": safety_message or "Vui lòng dừng lại và ưu tiên an toàn.",
            "safety_escalation": safety_level in {"moderate", "severe"},
            "used_llm": False,
        }

    context = _build_patient_context(db, user_id, exercise_type)

    # ── Format context as readable text (much better LLM comprehension than raw JSON) ──
    p = context.get("profile", {})
    ps = context.get("progress_summary", {})
    sessions = context.get("recent_sessions", [])
    errors = context.get("recurring_errors", [])
    progressions = context.get("recent_progressions", [])
    upcoming = context.get("upcoming_schedules", [])
    past_sched = context.get("past_schedules", [])
    limits = context.get("saved_limits", {})

    def fmt_session(s: Dict) -> str:
        mins = int((s.get("duration_seconds") or 0) // 60)
        return (
            f"  - {s.get('exercise_name','?')}: {s.get('total_reps',0)} reps, "
            f"chính xác {s.get('accuracy',0):.0f}%, {mins} phút"
        )

    trend_label = ""
    trend = ps.get("accuracy_trend")
    if trend is not None:
        if trend > 2:
            trend_label = f"cải thiện +{trend:.1f}%"
        elif trend < -2:
            trend_label = f"giảm {trend:.1f}%"
        else:
            trend_label = "ổn định"

    context_text = f"""=== HỒ SƠ BỆNH NHÂN ===
Tên: {p.get('full_name','?')}  |  Tuổi: {p.get('age','?')}  |  Giới tính: {p.get('gender','?')}
Mức đau: {p.get('pain_level','?')}/10  |  Vận động: {p.get('mobility_level','?')}
Chấn thương: {p.get('injury_type') or 'Không có'}
Bệnh nền: {p.get('medical_conditions') or 'Không có'}
BMI: {p.get('bmi','?')}

=== TIẾN TRÌNH ===
Tổng buổi tập: {ps.get('total_sessions',0)}
Độ chính xác trung bình: {ps.get('avg_accuracy',0):.1f}%  ({trend_label})
Bài tập đã tập: {', '.join(ps.get('unique_exercises',[]) or ['Chưa có'])}

=== 5 BUỔI GẦN NHẤT ===
{chr(10).join(fmt_session(s) for s in sessions[:5]) if sessions else '  Chưa có buổi tập nào'}

=== LỖI KỸ THUẬT THƯỜNG GẶP ===
{chr(10).join(f'  - {e["name"]}: {e["count"]} lần' for e in errors) if errors else '  Không có lỗi nổi bật'}

=== GIỚI HẠN CÁ NHÂN HOÁ ===
Reps tối đa/hiệp: {limits.get('max_reps_per_set') or 'Chưa đặt'}
Nghỉ giữa hiệp: {limits.get('recommended_rest_seconds') or 'Chưa đặt'} giây
Điểm khó: {limits.get('difficulty_score') or 'Chưa đặt'}

=== TĂNG CẤP ĐỘ GẦN ĐÂY ===
{chr(10).join(f'  - {pr["exercise_name"]}: {pr["prev_reps"]} → {pr["new_reps"]} reps (đã duyệt)' for pr in progressions) if progressions else '  Chưa có'}

=== LỊCH TẬP SẮP TỚI ===
{chr(10).join(f'  - {s["exercise_name"]}: {s["scheduled_for"]}' + (f' ({s["note"]})' if s.get("note") else '') for s in upcoming) if upcoming else '  Không có lịch tập nào'}

=== LỊCH TẬP ĐÃ QUA ===
{chr(10).join(f'  - {s["exercise_name"]}: {s["scheduled_for"]}' for s in past_sched) if past_sched else '  Không có'}"""

    # Build conversation history
    history_block = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history:
            role_label = "Bệnh nhân" if msg["role"] == "user" else "Huấn luyện viên"
            history_lines.append(f"{role_label}: {msg['content']}")
        history_block = (
            "\n=== LỊCH SỬ HỘI THOẠI ===\n"
            + "\n".join(history_lines[-12:])   # last 6 exchanges
            + "\n=== HẾT LỊCH SỬ ===\n"
        )

    system_prompt = (
        "Bạn là Huấn Luyện Viên Phục Hồi Chức Năng, người đồng hành đáng tin cậy của bệnh nhân cao tuổi. "
        "Giọng điệu: ân cần, rõ ràng, khích lệ — như nói chuyện với bố mẹ. "
        "Luôn trả lời bằng tiếng Việt, đúng trọng tâm, tối đa 180 từ trừ khi được yêu cầu chi tiết hơn.\n\n"

        "TÊN BÀI TẬP (LUÔN dùng tên tiếng Việt, KHÔNG bao giờ viết tên kỹ thuật ra):\n"
        "arm_raise → Nâng tay | squat → Squat | calf_raise → Nâng gót chân | single_leg_stand → Đứng một chân\n\n"

        "CÁCH PHÂN TÍCH DỮ LIỆU:\n"
        "- So sánh buổi gần nhất với trung bình để nhận xét cụ thể (VD: 'Buổi hôm qua đạt 85%, cao hơn mức trung bình 72% của bạn')\n"
        "- Dùng lỗi kỹ thuật để giải thích nguyên nhân độ chính xác thấp (VD: 'Lỗi gập gối quá ít chiếm 8 lần — đó là lý do chính khiến điểm giảm')\n"
        "- Dùng pain_level để điều chỉnh khuyến nghị (pain >= 7: đề nghị nghỉ; pain 4-6: giảm cường độ; pain <= 3: duy trì/tăng)\n"
        "- Dùng injury_type để cảnh báo đúng bài tập (VD: chấn thương vai → thận trọng với Nâng tay)\n"
        "- Dùng accuracy_trend: tăng = khen ngợi + đề xuất tiếp tục; giảm = tìm nguyên nhân từ lỗi kỹ thuật\n\n"

        "LỊCH TẬP:\n"
        "- Hỏi về lịch → chỉ liệt kê lịch từ dữ liệu, KHÔNG thêm hướng dẫn kỹ thuật\n"
        "- Không có lịch → báo 'Hiện chưa có lịch tập nào' rồi dừng\n\n"

        "TIẾN BỘ & ĐỘNG VIÊN:\n"
        "- Khi có tăng cấp độ mới: chúc mừng cụ thể ('Bác đã tăng từ X lên Y reps — thành tích tốt!')\n"
        "- Khi tiến trình đang tốt: ghi nhận và khích lệ tiếp tục\n"
        "- Khi tiến trình giảm: động viên nhẹ nhàng, giải thích nguyên nhân, đề xuất điều chỉnh cụ thể\n\n"

        "QUY TẮC:\n"
        "1. Trả lời ĐÚNG câu hỏi được hỏi, không thêm thông tin ngoài phạm vi\n"
        "2. Dùng số liệu thực từ hồ sơ để tư vấn — không nói chung chung\n"
        "3. Không chẩn đoán bệnh hoặc kê đơn thuốc\n"
        "4. Câu hỏi có/không → trả lời có/không trước, rồi giải thích ngắn\n\n"

        "ĐỊNH DẠNG:\n"
        "TUYỆT ĐỐI KHÔNG dùng: **, *, #, __\n"
        "Tiêu đề: chỉ viết hoa chữ đầu (VD: Tổng quan, Lỗi kỹ thuật)\n"
        "Hướng dẫn → đánh số 1. 2. 3.  |  Tóm tắt → gạch đầu dòng -  |  Câu hỏi thường → 1-3 câu trực tiếp\n\n"

        "AN TOÀN (chỉ khi người dùng báo triệu chứng):\n"
        "- Khó chịu nhẹ → giảm tốc độ, biên độ, số reps\n"
        "- Đau dai dẳng/sưng → dừng buổi tập, nghỉ ngơi, liên hệ bác sĩ\n"
        "- Đau ngực/chóng mặt/khó thở/tê liệt → dừng ngay, gọi cấp cứu"
    )

    # Build LLM messages with formatted context in system (not raw JSON in user)
    llm_messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": context_text},
    ]
    if history_block:
        llm_messages.append({"role": "system", "content": history_block})
    llm_messages.append({"role": "user", "content": user_message})

    import re as _re
    reply = _call_chat_completion(llm_messages)
    reply = reply.replace("**", "").replace("__", "")
    reply = _re.sub(r"^[•·▪▸➤]\s*", "- ", reply, flags=_re.MULTILINE)
    for tech in ["arm_raise", "squat", "calf_raise", "single_leg_stand"]:
        reply = reply.replace(f"({tech})", "").replace(f" {tech}", "")

    _save_message(
        db,
        user_id=user_id,
        role=ConversationRole.assistant,
        content=reply,
        metadata={"used_llm": True, "safety_escalation": False},
    )

    return {
        "reply": reply,
        "safety_escalation": False,
        "used_llm": True,
    }
