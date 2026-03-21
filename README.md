# Rehab AI - Full Stack

Hệ thống AI phục hồi chức năng cho người cao tuổi với FastAPI, React, MediaPipe Pose tracking, WebSocket realtime, và phân quyền bác sĩ/bệnh nhân.

## Công Nghệ
- Backend: FastAPI, SQLAlchemy, Alembic, MySQL, JWT
- Frontend: React + TypeScript + Vite

## Yêu Cầu Môi Trường
- Python 3.10+
- Node.js 18+
- MySQL 8+

## Cấu Hình Biến Môi Trường

### Backend
File mẫu: `backend/.env.example`

Biến chính:
- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_DAYS`

### Frontend
File mẫu: `frontend/.env.example`

Biến chính:
- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`

## Cài Đặt Nhanh (Windows)

1. Tạo database MySQL:
```sql
CREATE DATABASE rehab_v3;
```

2. Chạy script setup (tự tạo `.env` từ file mẫu nếu chưa có):
```cmd
setup-windows.bat
```

3. Mở backend:
```cmd
start-backend.bat
```

4. Mở frontend:
```cmd
start-frontend.bat
```

5. Truy cập:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Chạy Hệ Thống Bằng Docker 
Yêu cầu: Máy tính đã cài đặt và đang bật [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1. Chạy lệnh sau để tự động tải, cài đặt các thư viện và khởi chạy hệ thống (Database, Backend, Frontend):
```bash
docker-compose up --build -d
```
*(Tham số `-d` giúp chạy ngầm trong nền.)*

2. Chờ một lúc cho các tiến trình sẵn sàng, sau đó truy cập:
- **Frontend (Web App)**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs

3. Nếu muốn xem log để kiểm tra (ví dụ xem backend báo lỗi gì):
```bash
docker-compose logs -f
```

4. Để tắt hoàn toàn hệ thống khi không dùng nữa:
```bash
docker-compose down
```

**Lưu ý khi dùng Docker:** 
Nếu có sự thay đổi cập nhật code liên quan đến thư viện mới (add thêm package npm hoặc pip install thêm module mới), chạy lại lệnh `docker-compose up --build -d` để cập nhật môi trường.

## Cài Đặt Thủ Công

### Backend
```cmd
cd backend
python -m venv venv
```

Kích hoạt môi trường ảo:

- PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

- CMD:
```cmd
venv\Scripts\activate.bat
```

- Git Bash:
```bash
source venv/Scripts/activate
```

Sau khi đã kích hoạt venv:

```cmd
pip install -r requirements.txt
copy .env.example .env
python migrate_db.py
python main.py
```

### Frontend
```cmd
cd frontend
npm ci
copy .env.example .env
npm run dev
```

## Tài Khoản Mặc Định
- Bác sĩ: `doctor1 / doctor123`
- Bệnh nhân: `patient1 / patient123`

## Lưu Ý Cho Team Khi Pull
- Không commit `venv`, `.venv`, `node_modules`, `.env`, file database local.
- Luôn update từ `*.example` thành `.env` trên máy local.
- Khi backend thay đổi schema, chạy lại `python migrate_db.py`.
- Ưu tiên `npm ci` (khi có lock file) để đồng bộ version frontend.

## Troubleshooting
- Lỗi `RuntimeError: 'cryptography' package is required...`:
	- Kích hoạt đúng venv backend.
	- Chạy lại `pip install -r requirements.txt`.
	- Nếu vẫn lỗi, chạy thêm `pip install cryptography`.

## Tài Liệu Bổ Sung
- `Guide_alembic.md`
- `DATABASE_MANAGEMENT.md`
- `TECHNICAL_DOCUMENTATION.md`
