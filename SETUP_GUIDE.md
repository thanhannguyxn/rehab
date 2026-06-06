# Hướng Dẫn Setup và Chạy Hệ Thống AI Rehab

## Mục Lục
1. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
2. [Cài Đặt Nhanh](#cài-đặt-nhanh)
3. [Cài Đặt Thủ Công Chi Tiết](#cài-đặt-thủ-công-chi-tiết)
4. [Khắc Phục Lỗi Thường Gặp](#khắc-phục-lỗi-thường-gặp)
5. [Kiểm Tra Hệ Thống](#kiểm-tra-hệ-thống)
6. [Chạy Bằng Docker](#chạy-bằng-docker)

## Yêu Cầu Hệ Thống

### Phần Mềm Cần Thiết
- **Python 3.10+** (khuyến nghị 3.11)
- **Node.js 18+** và npm
- **MySQL 8.0+**
- **Git**

### Kiểm Tra Version
```bash
python --version
node --version
npm --version
mysql --version
```

## Cài Đặt Nhanh (Khuyến Nghị)

### Bước 1: Tạo Database MySQL
```sql
CREATE DATABASE rehab_v3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Bước 2: Chạy Script Setup Tự Động
```cmd
# Chạy trong thư mục gốc của dự án
setup-windows.bat
```

### Bước 3: Khởi Chạy Backend
```cmd
start-backend.bat
```

### Bước 4: Khởi Chạy Frontend (Terminal mới)
```cmd
start-frontend.bat
```

### Bước 5: Truy Cập Ứng Dụng
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Tài khoản test**:
  - Bác sĩ: `doctor1` / `doctor123`
  - Bệnh nhân: `patient1` / `patient123`

## Cài Đặt Thủ Công Chi Tiết

### Backend Setup

#### 1. Tạo và Kích Hoạt Virtual Environment
```cmd
cd backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt venv (chọn một trong các cách sau)

# PowerShell:
.\venv\Scripts\Activate.ps1

# CMD:
venv\Scripts\activate.bat

# Git Bash:
source venv/Scripts/activate
```

#### 2. Cài Đặt Dependencies
```cmd
# Đảm bảo pip mới nhất
python -m pip install --upgrade pip

# Cài đặt packages
pip install -r requirements.txt
```

#### 3. Cấu Hình Environment Variables
```cmd
# Copy file mẫu (nếu chưa có)
copy .env.example .env

# Chỉnh sửa file .env với thông tin database của bạn
notepad .env
```

**Nội dung file .env mẫu:**
```env
DATABASE_URL=mysql+pymysql://root:123456@localhost/rehab_v3
SECRET_KEY=your-super-secret-key-change-this
OPENAI_API_KEY=your-openai-api-key-optional
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
```

#### 4. Khởi Tạo Database
```cmd
# Chạy migration
python migrate_db.py

# Khởi chạy server
python main.py
```

### Frontend Setup

#### 1. Cài Đặt Dependencies
```cmd
cd frontend

# Cài đặt packages (khuyến nghị dùng npm ci nếu có package-lock.json)
npm ci
# hoặc
npm install
```

#### 2. Cấu Hình Environment (nếu cần)
```cmd
# Copy file mẫu nếu có
copy .env.example .env
```

#### 3. Khởi Chạy Development Server
```cmd
npm run dev
```

## Khắc Phục Lỗi Thường Gặp

### Lỗi Backend

#### 1. Lỗi `ModuleNotFoundError: No module named 'xyz'`
```cmd
# Đảm bảo venv được kích hoạt
venv\Scripts\activate

# Cài lại dependencies
pip install -r requirements.txt

# Nếu vẫn lỗi, cài từng module cụ thể
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv
```

#### 2. Lỗi Database Connection
```bash
# Kiểm tra MySQL service đang chạy
net start mysql
# hoặc
services.msc

# Kiểm tra database tồn tại
mysql -u root -p
SHOW DATABASES;
```

**Fix thông thường:**
- Đảm bảo MySQL đang chạy
- Kiểm tra username/password trong `.env`
- Tạo database `rehab_v3` nếu chưa có
- Kiểm tra port MySQL (mặc định 3306)

#### 3. Lỗi `ImportError: cannot import name 'limiter'`
```cmd
# Đảm bảo file limiter.py tồn tại trong thư mục backend
ls limiter.py

# Nếu thiếu, tạo file limiter.py:
```

**Tạo file `backend/limiter.py`:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

#### 4. Lỗi `cryptography` package
```cmd
# Kích hoạt venv và cài lại
venv\Scripts\activate
pip install --upgrade cryptography
pip install --upgrade passlib[bcrypt]
```

#### 5. Lỗi Port 8000 đã được sử dụng
```cmd
# Tìm process đang dùng port
netstat -ano | findstr :8000

# Kill process (thay PID bằng số thực tế)
taskkill /PID [PID_NUMBER] /F
```

### Lỗi Frontend

#### 1. Lỗi `npm install` Failed
```cmd
# Xóa cache và node_modules
npm cache clean --force
rmdir /S node_modules
del package-lock.json

# Cài lại
npm install
```

#### 2. Lỗi Port 3000 đã được sử dụng
```cmd
# Option 1: Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID [PID_NUMBER] /F

# Option 2: Chạy trên port khác
npm run dev -- --port 3001
```

#### 3. Lỗi CORS khi gọi API
Kiểm tra file `.env` frontend có đúng URL backend:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Lỗi Chung

#### 1. Lỗi Permission (Windows)
```cmd
# Chạy terminal as Administrator
# Hoặc thay đổi execution policy PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Python không được nhận diện
```cmd
# Thêm Python vào PATH environment variables
# Hoặc dùng python3 thay vì python
python3 --version
```

## Kiểm Tra Hệ Thống

### Kiểm Tra Backend Hoạt Động
```bash
# Test API endpoint
curl http://localhost:8000/api/auth/test
# hoặc mở browser: http://localhost:8000/docs
```

### Kiểm Tra Frontend Hoạt Động
```bash
# Mở browser: http://localhost:3000
# Đăng nhập với tài khoản test
```

### Kiểm Tra Database Connection
```python
# Chạy trong backend directory với venv activated
python -c "
from db.connection import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful!')
"
```

## Chạy Bằng Docker (Tùy Chọn)

### Yêu Cầu
- Docker Desktop đã được cài đặt và đang chạy

### Khởi Chạy
```bash
# Build và chạy tất cả services
docker-compose up --build -d

# Xem logs
docker-compose logs -f

# Dừng hệ thống
docker-compose down
```

## Scripts Hữu Ích

### Tạo file `quick-start.bat`:
```batch
@echo off
echo Starting Rehab AI System...

echo 1. Starting Backend...
start cmd /k "cd backend && venv\Scripts\activate && python main.py"

echo 2. Waiting for backend to start...
timeout /t 5

echo 3. Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo 4. Opening browser...
timeout /t 10
start http://localhost:3000

echo System started! Check terminals for any errors.
pause
```

### Tạo file `stop-all.bat`:
```batch
@echo off
echo Stopping all Rehab AI processes...

taskkill /f /im python.exe
taskkill /f /im node.exe

echo All processes stopped.
pause
```

## Hỗ Trợ Thêm

### Nếu Vẫn Gặp Lỗi:

1. **Kiểm tra logs chi tiết**: Chạy backend/frontend trong terminal để xem error messages đầy đủ

2. **Restart services**:
   - Restart MySQL service
   - Restart terminal/IDE
   - Restart Windows (nếu cần)

3. **Chạy tests**:
   ```cmd
   # Backend
   cd backend && python -m pytest

   # Frontend
   cd frontend && npm test
   ```

4. **Environment clean**: Xóa và tạo lại virtual environments

5. **Check system resources**: Đảm bảo đủ RAM và disk space

### Liên Hệ Hỗ Trợ
- Tạo issue trên GitHub repository
- Gửi screenshot lỗi cụ thể
- Bao gồm thông tin version Python/Node/OS

---

**Lưu ý**: Luôn backup dữ liệu quan trọng trước khi thực hiện các lệnh xóa hoặc reset!