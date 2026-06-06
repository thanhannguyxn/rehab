# Tính năng Tăng Cấp Độ Bài Tập Tự Động (Progression Suggestion)

## Tổng quan

Hệ thống tự động phát hiện khi bệnh nhân đạt độ chính xác cao (≥ 80%) trong 3 buổi tập liên tiếp của cùng một bài tập, sau đó tạo một **đề xuất tăng cấp độ** để bác sĩ xem xét và duyệt. Không có gì thay đổi tự động — bác sĩ luôn là người quyết định cuối cùng.

---

## Flow hoàn chỉnh

```
Bệnh nhân kết thúc buổi tập (POST /sessions/{id}/end)
    │
    ▼ (background task)
progression_service.check_and_create_suggestion()
    │
    ├── Lấy 3 buổi gần nhất của bài tập đó
    ├── Kiểm tra: tất cả accuracy ≥ 80% và total_reps > 0?
    ├── Kiểm tra: đã có suggestion pending/approved trong 7 ngày qua chưa?
    │
    ├── KHÔNG đủ điều kiện → dừng, không làm gì
    │
    └── ĐỦ điều kiện → tạo ProgressionSuggestion (status=pending)
            │
            ▼
        Bác sĩ thấy thông báo trong Doctor Assistant
            │
            ├── Duyệt → apply_suggestion() cập nhật UserExerciseLimits
            │              Patient Coach thông báo bệnh nhân đã được tăng cấp
            │
            └── Từ chối → status=rejected, limits giữ nguyên
```

---

## Các file đã thay đổi / tạo mới

| File | Thay đổi |
|------|----------|
| `backend/models/session.py` | Thêm model `ProgressionSuggestion` |
| `backend/models/__init__.py` | Export `ProgressionSuggestion` |
| `backend/services/progression_service.py` | **Tạo mới** — toàn bộ logic trigger + apply |
| `backend/routers/sessions.py` | Gọi progression check sau `end_session` |
| `backend/routers/doctor.py` | 3 endpoints mới: list / approve / reject |
| `backend/services/tools.py` | 2 tools mới cho Doctor Assistant |
| `backend/services/doctor_assistant_agent.py` | Cập nhật system prompt |
| `backend/services/patient_coach_agent.py` | Thêm `recent_progressions` vào context |
| `backend/db/connection.py` | Migration tạo bảng `progression_suggestions` |

---

## Model: `ProgressionSuggestion`

```sql
CREATE TABLE progression_suggestions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,   -- FK → users.id
    doctor_id           INTEGER NOT NULL,   -- FK → users.id
    exercise_name       VARCHAR(255) NOT NULL,

    -- Dữ liệu trigger
    trigger_session_count  INTEGER NOT NULL,  -- luôn = 3
    avg_accuracy           FLOAT NOT NULL,    -- avg của 3 buổi trigger
    trigger_session_ids    TEXT,              -- JSON list [session_id, ...]

    -- Snapshot giới hạn hiện tại (tại thời điểm tạo suggestion)
    current_reps           INTEGER,
    current_difficulty     FLOAT,
    current_rest_seconds   INTEGER,

    -- Giá trị đề xuất
    suggested_reps         INTEGER,
    suggested_difficulty   FLOAT,
    suggested_rest_seconds INTEGER,

    -- Workflow
    status       VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    doctor_note  TEXT,

    created_at   DATETIME NOT NULL,
    updated_at   DATETIME NOT NULL
);
```

---

## Logic trigger (`progression_service.py`)

### Điều kiện kích hoạt

```python
_SESSIONS_REQUIRED = 3       # số buổi liên tiếp cần đạt
_ACCURACY_THRESHOLD = 80.0   # % độ chính xác tối thiểu
_COOLDOWN_DAYS = 7           # cooldown tránh tạo suggestion trùng lặp
```

Tất cả 3 điều kiện phải đúng đồng thời:
1. Bệnh nhân có **≥ 3 buổi tập hợp lệ** (total_reps > 0) của bài tập đó
2. **Tất cả 3 buổi gần nhất** đều có accuracy ≥ 80%
3. **Không có suggestion pending/approved** trong vòng 7 ngày qua cho cùng bài tập đó

### Mức tăng cấp theo bài tập

| Bài tập | max_reps_per_set | difficulty_score | rest_seconds |
|---------|-----------------|-----------------|--------------|
| squat | +2 | +0.10 | -15 giây |
| arm_raise | +2 | +0.10 | -10 giây |
| calf_raise | +3 | +0.10 | -10 giây |
| single_leg_stand | +1 | +0.15 | -20 giây |

**Giới hạn an toàn:**
- `max_reps_per_set` ≥ 3
- `difficulty_score` ≤ 1.0
- `recommended_rest_seconds` ≥ 20 giây

---

## API Endpoints (Doctor)

### `GET /doctor/progression-suggestions?status=pending`
Lấy danh sách đề xuất. `status` có thể là `pending`, `approved`, `rejected` (bỏ trống = tất cả).

**Response:**
```json
{
  "suggestions": [
    {
      "id": 1,
      "patient_id": 5,
      "patient_name": "Tran Thi B",
      "exercise_name": "squat",
      "avg_accuracy": 87.5,
      "trigger_session_count": 3,
      "current_reps": 10,
      "suggested_reps": 12,
      "current_difficulty": 0.5,
      "suggested_difficulty": 0.6,
      "current_rest_seconds": 60,
      "suggested_rest_seconds": 45,
      "status": "pending",
      "created_at": "2026-06-07T10:00:00"
    }
  ]
}
```

### `POST /doctor/progression-suggestions/{id}/approve`
Duyệt đề xuất → cập nhật `UserExerciseLimits` ngay lập tức.

**Body (optional):**
```json
{ "note": "Bệnh nhân tiến bộ tốt, tăng cường độ phù hợp" }
```

### `POST /doctor/progression-suggestions/{id}/reject`
Từ chối đề xuất → limits không đổi.

**Body (optional):**
```json
{ "note": "Bệnh nhân còn đau, chưa nên tăng cấp" }
```

---

## Doctor Assistant Tools

Bác sĩ có thể hỏi chatbot bằng ngôn ngữ tự nhiên:

> **"Bệnh nhân nào đang sẵn sàng tăng cấp độ?"**
> → Bot gọi `list_progression_suggestions(status="pending")` và liệt kê

> **"Duyệt đề xuất số 3 cho tôi"**
> → Bot gọi `approve_progression_suggestion(suggestion_id=3)`

### Tool: `list_progression_suggestions`
```json
{
  "name": "list_progression_suggestions",
  "parameters": {
    "status": "pending"  // optional: pending | approved | rejected
  }
}
```

### Tool: `approve_progression_suggestion`
```json
{
  "name": "approve_progression_suggestion",
  "parameters": {
    "suggestion_id": 1,
    "note": "Ghi chú lâm sàng tùy chọn"  // optional
  }
}
```

> **Lưu ý:** Bot luôn gọi `list_progression_suggestions` trước để xác nhận `suggestion_id` trước khi duyệt.

---

## Patient Coach

Khi bệnh nhân chat với bot sau khi đã được tăng cấp độ, `_build_patient_context` sẽ trả về `recent_progressions` — danh sách tối đa 3 đề xuất đã được duyệt gần nhất. Bot sẽ:

- Chúc mừng bệnh nhân đã đạt được cấp độ mới
- Thông báo rõ bài tập nào, reps tăng từ bao nhiêu lên bao nhiêu
- Nhắc giữ kỹ thuật đúng khi tập với cường độ mới

---

## Ví dụ thực tế

**Bệnh nhân:** Tran Thi B (squat, current limits: 10 reps / difficulty 0.5 / rest 60s)

| Buổi | Accuracy |
|------|----------|
| #12 | 85% ✓ |
| #13 | 88% ✓ |
| #14 | 91% ✓ |

→ Sau buổi #14: `check_and_create_suggestion()` tạo suggestion với:
- `avg_accuracy = 88.0%`
- `suggested_reps = 12`
- `suggested_difficulty = 0.6`
- `suggested_rest_seconds = 45`

→ Bác sĩ mở Doctor Assistant: *"Có bệnh nhân nào sẵn sàng tăng cấp không?"*
→ Bot trả lời danh sách, bác sĩ duyệt
→ `UserExerciseLimits` cập nhật ngay
→ Lần sau bệnh nhân chat: bot chúc mừng và nhắc tập với 12 reps

---

## Ghi chú triển khai

- Bảng `progression_suggestions` được tạo tự động khi server khởi động qua `migrate_db()` trong `db/connection.py`
- Không cần Alembic — dùng `checkfirst=True` của SQLAlchemy
- Progression check chạy hoàn toàn trong **background task**, không ảnh hưởng response time của `end_session`
- Bài tập custom (không phải 4 bài mặc định) bị bỏ qua — chỉ áp dụng cho `squat`, `arm_raise`, `calf_raise`, `single_leg_stand`
