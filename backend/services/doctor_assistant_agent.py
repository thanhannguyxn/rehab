"""Doctor assistant agent with conversation memory, tool-calling, and LLM completion."""

import json
import re
import unicodedata
from datetime import timedelta, datetime
from typing import Any, Dict, List, Optional
from urllib import request as _url_request

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import User, DBSession, SessionError, UserRole, PatientSchedule, ChatMessage, ConversationRole
from settings import LLM_API_BASE_URL, LLM_API_KEY, LLM_MODEL
from services.tools import TOOL_DEFINITIONS, TOOL_NAMES, execute_tool, build_tool_result_message

_AGENT_TYPE = "doctor_assistant"
_MAX_HISTORY_MESSAGES = 20

# ---------------------------------------------------------------------------
# Scheduling helpers (retained as fallback / lightweight path)
# ---------------------------------------------------------------------------

_EXERCISE_ALIASES = {
    "arm_raise": [
        "arm_raise", "arm raise", "arm-raise",
        "nâng tay", "nang tay", "giơ tay", "gio tay",
        "nâng cánh tay", "nang canh tay",
    ],
    "squat": ["squat", "gập gối", "gap goi", "ngồi xổm", "ngoi xom"],
    "calf_raise": [
        "calf_raise", "calf raise", "calf-raise",
        "nâng gót chân", "nang got chan",
        "nâng gót", "nang got",
        "nâng bắp chân", "nang bap chan",
    ],
    "single_leg_stand": [
        "single_leg_stand", "single leg stand", "single-leg-stand",
        "đứng một chân", "dung mot chan",
        "đứng 1 chân", "dung 1 chan",
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
                "Tôi phát hiện yêu cầu lên lịch, nhưng không xác định được loại bài tập. "
                "Vui lòng sử dụng một trong các loại: arm_raise, squat, calf_raise, single_leg_stand."
            ),
            "used_llm": False,
        }

    patient_ref = _extract_patient_reference(user_message)
    if not patient_ref:
        return {
            "reply": "Tôi phát hiện yêu cầu lên lịch, nhưng không xác định được tên bệnh nhân sau 'for/cho'.",
            "used_llm": False,
        }

    patient = _find_patient_for_doctor(db, doctor_id, patient_ref)
    if not patient:
        return {
            "reply": (
                f"Không tìm thấy bệnh nhân '{patient_ref}' trong danh sách của bạn. "
                "Vui lòng sử dụng đúng họ tên bệnh nhân được hiển thị trong danh sách."
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
                f"Đã tồn tại lịch tập cho {patient.full_name}: {exercise_name} vào "
                f"{scheduled_for.strftime('%Y-%m-%d')}. Tôi không tạo bản trùng lặp."
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
            f"Đã tạo lịch tập thành công cho {patient.full_name}: {exercise_name} vào "
            f"{scheduled_for.strftime('%Y-%m-%d')}. Bệnh nhân sẽ thấy lịch này khi đăng nhập."
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
        patient_summary_list.append({
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
        })

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


# ---------------------------------------------------------------------------
# Conversation memory helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# LLM call helper (supports tool-calling)
# ---------------------------------------------------------------------------

def _call_llm_with_tools(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call OpenAI-compatible API (Groq) with tool calling support."""
    if not LLM_API_KEY:
        return {
            "content": (
                "Trợ lý bác sĩ đã được cấu hình nhưng thiếu LLM_API_KEY. "
                "Vui lòng đặt giá trị trong backend/.env."
            ),
            "tool_call": None,
        }

    endpoint = LLM_API_BASE_URL.rstrip("/") + "/chat/completions"
    payload: Dict[str, Any] = {
        "model": LLM_MODEL,
        "temperature": 0.4,
        "max_tokens": 1200,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
    }

    req = _url_request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_API_KEY}",
            "User-Agent": "Mozilla/5.0 (compatible; rehab-chatbot/1.0)",
        },
        method="POST",
    )

    from urllib import error as _url_error
    import time as _time

    for attempt in range(2):
        try:
            with _url_request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
                choice = data["choices"][0]
                msg = choice["message"]
                tool_calls = msg.get("tool_calls") or []
                return {
                    "content": msg.get("content") or "",
                    "tool_call": tool_calls[0] if tool_calls else None,
                    "finish_reason": choice.get("finish_reason"),
                }
        except _url_error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            try:
                err_msg = json.loads(body).get("error", {}).get("message", "")
            except Exception:
                err_msg = body[:200]
            if exc.code == 429:
                if attempt == 0:
                    _time.sleep(2)
                    continue
                return {
                    "content": "API đã đạt giới hạn tốc độ. Vui lòng thử lại sau vài giây.",
                    "tool_call": None,
                    "finish_reason": "error",
                }
            if exc.code in (401, 403):
                return {
                    "content": f"API key không hợp lệ (HTTP {exc.code}). Vui lòng kiểm tra cấu hình.",
                    "tool_call": None,
                    "finish_reason": "error",
                }
            return {
                "content": f"Lỗi API HTTP {exc.code}: {err_msg or 'Không có chi tiết.'}",
                "tool_call": None,
                "finish_reason": "error",
            }
        except Exception as exc:
            return {
                "content": f"Không thể kết nối dịch vụ AI ({type(exc).__name__}). Vui lòng thử lại.",
                "tool_call": None,
                "finish_reason": "error",
            }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_doctor_assistant_reply(
    db: Session,
    doctor_id: int,
    user_message: str,
    patient_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate doctor assistant reply with:
    - Conversation memory (loaded from / saved to DB)
    - Tool-calling (create_patient_schedule, list_doctor_patients, get_patient_details)
    - Regex-based scheduling fallback for simple commands
    """
    # Try lightweight regex scheduling first (no LLM needed)
    command_result = _try_create_schedule_from_message(db, doctor_id, user_message)
    if command_result is not None:
        # Still save the exchange for history
        _save_message(db, doctor_id, ConversationRole.user, user_message, {"used_llm": False})
        _save_message(db, doctor_id, ConversationRole.assistant, command_result["reply"], {"used_llm": False})
        return command_result

    # Load history before saving the new user message
    conversation_history = _load_conversation_history(db, doctor_id)

    # Persist user message immediately
    _save_message(
        db,
        user_id=doctor_id,
        role=ConversationRole.user,
        content=user_message,
        metadata={"patient_id": patient_id},
    )

    context = _build_doctor_context(db, doctor_id, patient_id)

    # ── Format context as readable text ──
    doc = context.get("doctor_profile", {})
    practice = context.get("practice_summary", {})
    patient_list = context.get("patient_summary_list", [])
    selected = context.get("selected_patient")

    def risk_flag(p: Dict) -> str:
        flags = []
        if p.get("session_count", 0) == 0:
            flags.append("chưa tập lần nào")
        if (p.get("pain_level") or 0) >= 7:
            flags.append(f"đau cao ({p['pain_level']}/10)")
        if (p.get("avg_accuracy") or 0) < 60 and p.get("session_count", 0) > 0:
            flags.append("kỹ thuật yếu (<60%)")
        last = p.get("last_session")
        if last and last.get("start_time"):
            try:
                days_ago = (datetime.utcnow() - datetime.fromisoformat(last["start_time"])).days
                if days_ago > 7:
                    flags.append(f"không tập {days_ago} ngày")
            except Exception:
                pass
        return " | ".join(flags) if flags else "ổn"

    patient_rows = "\n".join(
        f"  [{p['patient_id']}] {p['full_name']} — {p['session_count']} buổi, "
        f"chính xác TB {p['avg_accuracy']:.0f}%, đau {p.get('pain_level','?')}/10 → {risk_flag(p)}"
        for p in patient_list
    ) or "  Chưa có bệnh nhân"

    selected_text = ""
    if selected:
        err_lines = "\n".join(
            f"    - {e['name']}: {e['count']} lần"
            for e in selected.get("recurring_errors", [])
        ) or "    Không có"
        sess_lines = "\n".join(
            f"    - {s['exercise_name']}: {s['total_reps']} reps, {s['accuracy']:.0f}%"
            for s in selected.get("recent_sessions", [])[:5]
        ) or "    Chưa có"
        selected_text = f"""
=== BỆNH NHÂN ĐANG XEM: {selected['full_name']} (ID {selected['patient_id']}) ===
Tuổi: {selected.get('age','?')}  |  Giới tính: {selected.get('gender','?')}
Mức đau: {selected.get('pain_level','?')}/10  |  Vận động: {selected.get('mobility_level','?')}
Chấn thương: {selected.get('injury_type') or 'Không có'}
Bệnh nền: {selected.get('medical_conditions') or 'Không có'}

5 buổi tập gần nhất:
{sess_lines}

Lỗi kỹ thuật thường gặp:
{err_lines}"""

    context_text = f"""=== THÔNG TIN BÁC SĨ ===
Tên: {doc.get('full_name','?')}  |  Tổng bệnh nhân: {practice.get('total_patients',0)}

=== DANH SÁCH BỆNH NHÂN ===
{patient_rows}
{selected_text}"""

    # Build conversation history
    history_block = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history:
            role_label = "Bác sĩ" if msg["role"] == "user" else "Trợ lý"
            history_lines.append(f"{role_label}: {msg['content']}")
        history_block = (
            "\n=== LỊCH SỬ HỘI THOẠI ===\n"
            + "\n".join(history_lines[-12:])
            + "\n=== HẾT LỊCH SỬ ===\n"
        )

    system_prompt = (
        "Bạn là Trợ Lý Bác Sĩ Phục Hồi Chức Năng chuyên nghiệp và sắc bén. "
        "Trả lời bằng tiếng Việt, dựa HOÀN TOÀN vào dữ liệu thực tế được cung cấp — không bịa số liệu.\n\n"

        "TÊN BÀI TẬP — TUYỆT ĐỐI KHÔNG viết arm_raise, squat, calf_raise, single_leg_stand trong câu trả lời:\n"
        "arm_raise → Nâng tay | squat → Squat | calf_raise → Nâng gót chân | single_leg_stand → Đứng một chân\n"
        "Chỉ dùng tên kỹ thuật khi GỌI TOOL, không bao giờ hiển thị ra ngoài.\n\n"
        "TÊN TRƯỜNG DỮ LIỆU — KHÔNG viết pain_level, session_count, avg_accuracy, accuracy ra câu trả lời:\n"
        "pain_level → mức đau | session_count → số buổi tập | avg_accuracy/accuracy → độ chính xác\n\n"

        "PHÂN TÍCH LÂM SÀNG — luôn suy luận từ dữ liệu:\n"
        "- Tuân thủ: session_count thấp hoặc không tập >7 ngày = nguy cơ bỏ điều trị → đề xuất nhắc nhở\n"
        "- Kỹ thuật: avg_accuracy <60% = cần hướng dẫn lại; >90% ổn định = sẵn sàng tăng cường độ\n"
        "- Đau & rủi ro: pain_level ≥7 = cần đánh giá lại; kết hợp injury_type để cá nhân hoá\n"
        "- Lỗi tái diễn: recurring_errors cao → chỉ ra nguyên nhân cụ thể và phương án can thiệp\n"
        "- Khi phân tích nhiều bệnh nhân: ưu tiên liệt kê người có rủi ro cao nhất trước\n\n"

        "CÔNG CỤ — gọi chủ động khi cần thông tin chi tiết hơn:\n"
        "- list_doctor_patients: tổng quan tất cả bệnh nhân\n"
        "- get_patient_details(patient_id): chi tiết đầy đủ 1 bệnh nhân\n"
        "- create_patient_schedule(patient_id, exercise_name, scheduled_for, note): lên lịch tập\n"
        "- list_progression_suggestions(status): xem đề xuất tăng cấp (pending/approved/rejected)\n"
        "- approve_progression_suggestion(suggestion_id, note): duyệt tăng cấp độ\n\n"

        "QUY TẮC:\n"
        "1. Chỉ dùng số liệu thực — nếu thiếu dữ liệu, nói rõ 'chưa có dữ liệu' thay vì ước đoán\n"
        "2. Sau khi tool trả kết quả: phân tích lâm sàng ngay, không liệt kê dữ liệu thô\n"
        "3. Không kê đơn thuốc hoặc chẩn đoán bệnh chính thức\n"
        "4. Câu hỏi ngắn → trả lời thẳng 1-3 câu\n\n"

        "ĐỊNH DẠNG:\n"
        "KHÔNG dùng: **, *, #, __  |  Bullet: dấu -  |  Tiêu đề: chỉ viết hoa chữ đầu\n\n"
        "Cho phân tích bệnh nhân đầy đủ, dùng cấu trúc:\n"
        "Nhận xét chính\n"
        "[1-2 câu tóm tắt tình trạng nổi bật, dùng số liệu cụ thể]\n\n"
        "Đề xuất tiếp theo\n"
        "- [hành động cụ thể với lý do]\n"
        "- [hành động cụ thể với lý do]\n\n"
        "Rủi ro cần lưu ý\n"
        "- [cảnh báo cụ thể dựa trên dữ liệu]\n\n"
        "Chỉ số theo dõi\n"
        "- [chỉ số: mục tiêu cụ thể trong X tuần]"
    )

    llm_messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": context_text},
    ]
    if history_block:
        llm_messages.append({"role": "system", "content": history_block})
    llm_messages.append({"role": "user", "content": user_message})

    # First LLM call
    response = _call_llm_with_tools(llm_messages)

    # Handle tool calls: execute up to 5 rounds to allow chained calls
    max_rounds = 5
    current_content = response.get("content") or ""
    tool_call = response.get("tool_call")  # OpenAI format: {"id": "...", "function": {"name": "...", "arguments": "..."}}

    for _round in range(max_rounds):
        if tool_call is None:
            break

        tool_name = tool_call.get("function", {}).get("name", "")
        if tool_name not in TOOL_NAMES:
            current_content += f"\n[Công cụ không xác định '{tool_name}' bị bỏ qua]"
            break

        raw_args = tool_call["function"].get("arguments", "{}")
        try:
            arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            current_content += "\n[Tham số công cụ không hợp lệ]"
            break

        tool_result = execute_tool(db, doctor_id, tool_name, arguments)
        tool_result_str = build_tool_result_message(tool_result)

        llm_messages.append({
            "role": "assistant",
            "content": current_content or None,
            "tool_calls": [tool_call],
        })
        llm_messages.append({
            "role": "tool",
            "tool_call_id": tool_call.get("id", ""),
            "content": tool_result_str,
        })

        response = _call_llm_with_tools(llm_messages)
        current_content = response.get("content") or ""
        tool_call = response.get("tool_call")

    # Strip disallowed formatting
    import re as _re
    final_reply = current_content.strip()
    final_reply = final_reply.replace("**", "").replace("__", "")
    # Replace bullet variants with dash
    final_reply = _re.sub(r"^[•·▪▸➤]\s*", "- ", final_reply, flags=_re.MULTILINE)
    # Remove technical names shown in parentheses after Vietnamese names
    for tech, viet in [
        ("arm_raise", "Nâng tay"), ("squat", "Squat"),
        ("calf_raise", "Nâng gót chân"), ("single_leg_stand", "Đứng một chân"),
    ]:
        final_reply = final_reply.replace(f"({tech})", "").replace(f" {tech}", f" {viet}")
    # Replace field name labels with natural Vietnamese
    field_map = {
        "pain_level": "mức đau", "Pain_level": "Mức đau",
        "session_count": "số buổi tập", "Session_count": "Số buổi tập",
        "avg_accuracy": "độ chính xác trung bình", "accuracy": "độ chính xác",
        "Accuracy": "Độ chính xác",
    }
    for eng, vi in field_map.items():
        final_reply = final_reply.replace(eng, vi)
    if not final_reply:
        final_reply = (
            "Tôi đã xử lý yêu cầu của bạn nhưng không tạo được phản hồi. "
            "Vui lòng thử diễn đạt lại câu hỏi của bạn."
        )

    # Persist assistant reply
    _save_message(
        db,
        user_id=doctor_id,
        role=ConversationRole.assistant,
        content=final_reply,
        metadata={"used_llm": True},
    )

    return {
        "reply": final_reply,
        "used_llm": True,
    }
