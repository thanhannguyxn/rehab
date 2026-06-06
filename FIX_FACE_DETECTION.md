# FIX LỖI NHẬN DIỆN KHUÔN MẶT & CHẠY HỆ THỐNG

## LỖI ĐÃ FIX

### Lỗi MediaPipe (Nhận Diện Khuôn Mặt & Tư Thế)

**Vấn đề**:
```
AttributeError: module 'mediapipe' has no attribute 'solutions'
```

**Nguyên nhân**: MediaPipe version 0.10.33 đã loại bỏ API `solutions` (legacy API)

**Giải pháp**: Downgrade xuống MediaPipe 0.10.5 (có solutions API)

**ĐÃ FIX XONG** - Backend đã được cập nhật và chạy thành công!

---

## CÁCH CHẠY HỆ THỐNG

### Phương Án 1: Dùng Script Tự Động (KHUYẾN NGHỊ)

```cmd
# Chạy file này từ thư mục gốc dự án
start-system.bat
```

Script sẽ tự động:
- Kích hoạt virtual environment
- Khởi chạy Backend (mở terminal riêng)
- Khởi chạy Frontend (mở terminal riêng)

### Phương Án 2: Chạy Thủ Công

**Terminal 1 - Backend:**
```cmd
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```cmd
cd frontend
npm run dev
```

### Phương Án 3: Fix Lại Từ Đầu (Nếu Vẫn Lỗi)

```cmd
cd backend
backend\start-with-fix.bat
```

---

## TRUY CẬP ỨNG DỤNG

Sau khi chạy xong:

- **Frontend**: http://localhost:3000 (hoặc 3002 nếu 3000 bị chiếm)
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000

### Tài Khoản Demo

| Vai Trò    | Username  | Password   |
|------------|-----------|------------|
| Bác sĩ     | doctor1   | doctor123  |
| Bệnh nhân  | patient1  | patient123 |

---

## CHI TIẾT NHỮNG GÌ ĐÃ ĐƯỢC FIX

### 1. MediaPipe Version
```bash
# ĐÃ CẬP NHẬT requirements.txt:
mediapipe==0.10.5  # (trước đây: 0.10.33)
```

### 2. Face Service
- `services/face_service.py` - Hoạt động với mediapipe 0.10.5
- Nhận diện cảm xúc: đau, mệt, vui, tập trung
- Calibration tự động trong 30 frames đầu

### 3. Pose Service
- `services/pose_service.py` - Hoạt động với mediapipe 0.10.5
- Nhận diện tư thế và đếm số lần tập
- Tính góc cử động

### 4. Database
- MySQL connection thành công
- Migration đã chạy
- Tables đã được tạo

---

## KIỂM TRA HỆ THỐNG

### Test Backend API:
```bash
# Mở browser hoặc curl
curl http://localhost:8000/docs
```

### Test Imports:
```bash
cd backend
venv\Scripts\activate
python -c "from services.face_service import face_service; from services.pose_service import pose; print('OK')"
```

---

## CÁC LỖI CÓ THỂ GẶP VÀ CÁCH FIX

### Lỗi 1: Port 8000 đã được sử dụng

**Hiện tượng**: `error while attempting to bind on address ('0.0.0.0', 8000)`

**Fix**:
```cmd
# Tìm và kill process
netstat -ano | findstr :8000
taskkill //PID [PID_NUMBER] //F
```

### Lỗi 2: Virtual Environment chưa kích hoạt

**Hiện tượng**: `ModuleNotFoundError`

**Fix**:
```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Lỗi 3: MediaPipe không tương thích

**Hiện tượng**: `AttributeError: module 'mediapipe' has no attribute 'solutions'`

**Fix**:
```cmd
cd backend
venv\Scripts\activate
pip install mediapipe==0.10.5
```

### Lỗi 4: MySQL không kết nối được

**Hiện tượng**: `Can't connect to MySQL server`

**Fix**:
```cmd
# 1. Kiểm tra MySQL service
net start mysql80

# 2. Tạo database nếu chưa có
mysql -u root -p
CREATE DATABASE rehab_v3;
exit

# 3. Chạy lại migration
cd backend
venv\Scripts\activate
python migrate_db.py
```

### Lỗi 5: Frontend không build được

**Hiện tượng**: Node modules errors

**Fix**:
```cmd
cd frontend
rmdir /S node_modules
del package-lock.json
npm install
npm run dev
```

---

## TÍNH NĂNG NHẬN DIỆN CẢM XÚC

Hệ thống đã được fix và có thể nhận diện:

| Cảm xúc | Mô tả | Độ chính xác |
|---------|-------|--------------|
| HAPPY | Mắt mở rộng + miệng cười | Cao |
| NEUTRAL | Khuôn mặt bình thường | Cao |
| PAIN | Nhíu mày + mắt nhắm + miệng cong xuống | Trung bình |
| STRUGGLING | Mắt hơi nhắm + nhíu mày | Trung bình |
| TIRED | Mắt lơ đãng + chán nản | Trung bình |
| FOCUSED | Nhíu mày nhẹ + tập trung | Trung bình |

### Calibration
- Hệ thống tự động calibrate trong 30 frames đầu
- Tạo baseline cho từng người dùng
- Phát hiện sự thay đổi tương đối

---

## KIỂM TRA CHỨC NĂNG

### 1. Đăng Nhập
- Vào http://localhost:3000 (hoặc port frontend đang chạy)
- Login với tài khoản doctor1/doctor123

### 2. Test Nhận Diện
- Vào trang Exercise Session
- Bật camera
- Hệ thống sẽ hiển thị:
  - Pose landmarks (xương khớp)
  - Face mesh (lưới khuôn mặt)
  - Emotion state (trạng thái cảm xúc)
  - Pain/Fatigue level (mức độ đau/mệt)

---

## HỖ TRỢ THÊM

Nếu vẫn gặp lỗi:

1. **Check logs**: Xem terminal backend và frontend
2. **Restart**: Đóng tất cả terminals và chạy lại `start-system.bat`
3. **Clean install**: Xóa venv và node_modules, cài lại từ đầu

### Lấy logs chi tiết:
```cmd
# Backend logs
cd backend
venv\Scripts\activate
python main.py > backend.log 2>&1

# Frontend logs
cd frontend
npm run dev > frontend.log 2>&1
```

---

**HỆ THỐNG ĐÃ ĐƯỢC FIX VÀ SẴN SÀNG SỬ DỤNG!**
