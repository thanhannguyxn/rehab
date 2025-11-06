# 🏥 Hệ Thống Phục Hồi Chức Năng V3 - Full Stack

Hệ thống AI phục hồi chức năng hoàn chỉnh cho người cao tuổi với MediaPipe Pose tracking.

## 🎯 Tính Năng Chính

### 👤 Bệnh Nhân
- ✅ Tập luyện với AI tracking real-time
- ✅ Skeleton overlay trực quan
- ✅ Feedback tức thì
- ✅ Lịch sử và biểu đồ tiến độ
- ✅ UI thân thiện (font 18px+, nút lớn, tương phản cao)

### 🏥 Bác Sĩ
- ✅ Dashboard quản lý bệnh nhân
- ✅ Xem chi tiết tiến độ từng bệnh nhân
- ✅ Biểu đồ phân tích
- ✅ Xuất báo cáo PDF
- ✅ Theo dõi lỗi thường gặp

## 🚀 Cài Đặt Nhanh (Windows)

### Bước 1: Cài Backend
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
✅ Backend: http://localhost:8000

### Bước 2: Cài Frontend
```cmd
cd frontend
npm install
npm run dev
```
✅ Frontend: http://localhost:3000

### Bước 3: Đăng Nhập
- Bác sĩ: doctor1 / doctor123
- Bệnh nhân: patient1 / patient123

## 💻 Tech Stack
- Backend: FastAPI + SQLite + MediaPipe + JWT
- Frontend: React + TypeScript + Tailwind + Recharts

## 📚 Documentation
Chi tiết xem trong thư mục frontend/README.md

---
**Made with ❤️ for elderly rehabilitation**
