# Phân Tích Đau Qua Khuôn Mặt (Post-Session Face Pain Analysis)

## Tổng quan

Hệ thống phân tích biểu hiện đau và mệt mỏi trên khuôn mặt bệnh nhân **sau khi kết thúc buổi tập**, không phải trong lúc tập. Cách thiết kế này đảm bảo quá trình nhận diện xương (pose tracking) không bị ảnh hưởng về hiệu suất.

---

## Luồng hoạt động

```
[Browser / WebSocket]
        │
        │  Gửi frame ảnh liên tục (JPEG base64)
        ▼
[backend/routers/websocket.py]
        │
        │  Lấy mẫu 1 frame mỗi 5 giây → buffer_frame(session_id, jpeg_bytes)
        ▼
[backend/services/session_runtime.py]  ← _frame_buffers (in-memory)
        │
        │  Khi bệnh nhân bấm "Kết thúc buổi tập"
        ▼
[POST /api/sessions/{id}/end]
        │
        │  pop_frame_buffer(session_id) → danh sách JPEG bytes
        │  background_tasks.add_task(analyze_session_pain, ...)
        ▼
[backend/services/pain_analysis_task.py]  ← chạy nền, không block response
        │
        │  Với mỗi frame: asyncio.to_thread(analyzer.analyze_frame, bgr)
        ▼
[backend/services/face_service.py]  ← FacePainAnalyzer (MediaPipe FaceMesh)
        │
        │  Ghi kết quả vào DB
        ▼
[Bảng sessions]  avg_pain_level, avg_fatigue_level, predominant_emotion, ...
```

---

## Các file liên quan

| File | Vai trò |
|------|---------|
| `backend/services/face_service.py` | Phân tích 1 frame ảnh bằng FaceMesh, trả về điểm đau/mệt |
| `backend/services/pain_analysis_task.py` | Background task async: xử lý tất cả frame, tổng hợp, ghi DB |
| `backend/services/session_runtime.py` | Quản lý bộ đệm frame (`buffer_frame`, `pop_frame_buffer`) |
| `backend/routers/websocket.py` | Lấy mẫu 1 frame/5s trong quá trình stream, gọi `buffer_frame` |
| `backend/routers/sessions.py` | Kích hoạt background task khi session kết thúc |
| `backend/models/session.py` | 5 cột DB lưu kết quả phân tích |
| `frontend/src/components/SessionCard.tsx` | Hiển thị badge đau/mệt trong lịch sử buổi tập |
| `frontend/src/pages/PatientHistory.tsx` | Banner tổng hợp thống kê đau toàn bộ lịch sử |

---

## Cơ chế phân tích (FacePainAnalyzer)

**Thư viện:** MediaPipe FaceMesh — 478 landmarks, không cần huấn luyện model

### Các chỉ số đo lường

#### 1. Eye Aspect Ratio (EAR) — Mức nheo mắt
```
EAR = chiều_cao_mắt / chiều_rộng_mắt
```
- Mắt bình thường: EAR ≈ 0.25
- Khi đau: mắt nheo lại → EAR giảm → `squint_score` tăng

Landmarks sử dụng:
- Mắt trái: 159 (trên), 145 (dưới), 33 (trong), 133 (ngoài)
- Mắt phải: 386 (trên), 374 (dưới), 263 (trong), 362 (ngoài)

#### 2. Brow Depression — Mức nhíu mày
```
brow_score = 1 - (khoảng_cách_mày_đến_mắt / face_height / 0.12)
```
- Bình thường: khoảng cách mày-mắt ≈ 5–9% chiều cao mặt
- Khi đau: mày hạ xuống → khoảng cách giảm → `brow_score` tăng

Landmarks: 105 (mày trái giữa), 334 (mày phải giữa)

#### 3. Lip Compression — Mức mím môi
```
MAR = chiều_cao_miệng / chiều_rộng_miệng
lip_score = (0.06 - MAR) / 0.06  (khi MAR < 0.06, else 0)
```
- Bình thường: môi hé nhẹ, MAR ≈ 0.04–0.10
- Khi đau: môi mím chặt → MAR → 0 → `lip_score` tăng

Landmarks: 13 (môi trên), 14 (môi dưới), 78 (trái), 308 (phải)

#### 4. Jaw Slack — Miệng há (dấu hiệu mệt)
- Điểm cao nhất khi MAR ≈ 0.20 (hé miệng tự nhiên khi mệt)
- Dùng hàm Gaussian: `exp(-((MAR - 0.20)² / 0.024))`

---

### Công thức tính điểm

```python
# Điểm đau (0.0 – 1.0)
pain_score = 0.40 * squint_score
           + 0.35 * brow_score
           + 0.25 * lip_score

# Điểm mệt (0.0 – 1.0)
droop = max(0, squint_score - brow_score * 0.5)   # mắt xụ mà không nhíu mày
fatigue_score = 0.55 * droop
              + 0.30 * jaw_score
              + 0.15 * max(0, squint_score - brow_score)
```

### Phân loại biểu cảm

| Điều kiện | Nhãn (`expression`) |
|-----------|---------------------|
| `pain_score > 0.55` | `"pain"` — Đau |
| `pain_score > 0.35` | `"discomfort"` — Khó chịu |
| `fatigue_score > 0.50` | `"tired"` — Mệt |
| Còn lại | `"neutral"` — Bình thường |

---

## Cơ chế bộ đệm frame

```python
# session_runtime.py
MAX_FRAMES = 30                          # tối đa 30 frame / session
# Với lấy mẫu 1 frame/5s → đủ cho buổi tập 2.5 phút
# Nếu session dài hơn, frame cũ bị loại bỏ (FIFO)
```

**Lưu ý quan trọng:** `buffer_frame` được gọi **trước** khi decode frame cho pose detection. Ngay cả khi OpenCV không decode được frame (môi trường ánh sáng xấu, góc camera lạ), JPEG bytes gốc vẫn được lưu vào buffer để FaceMesh xử lý riêng.

---

## Các cột DB lưu kết quả

```sql
-- Bảng sessions
avg_pain_level      FLOAT        -- Trung bình điểm đau (0.0–1.0)
avg_fatigue_level   FLOAT        -- Trung bình điểm mệt (0.0–1.0)
predominant_emotion VARCHAR(50)  -- Biểu cảm phổ biến nhất trong buổi
pain_incidents      INTEGER      -- Số frame có pain_score > 0.55
fatigue_incidents   INTEGER      -- Số frame có fatigue_score > 0.50
```

Tất cả 5 cột đã tồn tại trong schema, **không cần migration**.

Giá trị `NULL` = chưa có dữ liệu (session cũ hoặc không phát hiện khuôn mặt).

---

## Hiển thị trên giao diện

### SessionCard — Badge đau/mệt

| Badge | Điều kiện | Màu |
|-------|-----------|-----|
| 😊 Tốt | `pain < 0.35` và `fatigue < 0.50` | Xanh lá |
| 😴 Mệt | `fatigue ≥ 0.50` | Vàng |
| 😟 Khó chịu | `pain ≥ 0.35` | Cam |
| 😣 Đau | `pain ≥ 0.55` | Đỏ |
| 😐 Chưa có phân tích | `avg_pain_level = null` | Xám (nét đứt) |

Dưới badge hiển thị thêm:
- Số lần đau / số frame phân tích
- Phần trăm đau trung bình và mệt trung bình

### PatientHistory — Banner tổng hợp

Hiện phía trên danh sách buổi tập nếu có ít nhất 1 buổi đã phân tích:
- Điểm đau trung bình (toàn lịch sử)
- Số buổi có dấu hiệu đau
- Buổi tập đau nhất
- Chip cảnh báo "Nên tham khảo bác sĩ" nếu trung bình đau > 35%

---

## Hiệu suất & thiết kế

- **Không block session**: Toàn bộ FaceMesh chạy trong `BackgroundTasks` sau khi response đã trả về cho client
- **Không block event loop**: FaceMesh (CPU-intensive) chạy trong thread pool qua `asyncio.to_thread`
- **Lazy init**: FaceMesh singleton chỉ khởi động lần đầu tiên được gọi
- **Thread-safe**: Bộ đệm frame dùng `threading.Lock`
- **Bộ nhớ có giới hạn**: Tối đa 30 frame/session, tự động xóa sau khi session kết thúc

---

## Log server

```
[sessions]     Scheduled pain analysis for session 70 (3 frames)
[pain_analysis] Starting analysis for session 70 (3 frames)
[pain_analysis] Session 70 result: pain=0.123, fatigue=0.087, expression=neutral, pain_incidents=0, fatigue_incidents=0
[pain_analysis] Session 70: DB updated successfully.
```

Nếu không phát hiện khuôn mặt trong frame nào:
```
[pain_analysis] Session 70: no face detected in any frame. Pain fields left as NULL.
```
