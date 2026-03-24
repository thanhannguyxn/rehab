# ⚡ Khắc Phục Lỗi Backend Nhanh

## 🔍 Chẩn Đoán Nhanh

### Bước 1: Kiểm tra Virtual Environment
```cmd
cd backend

# Kiểm tra venv có tồn tại không
dir venv

# Nếu không có, tạo venv mới
python -m venv venv

# Kích hoạt venv
venv\Scripts\activate

# Kiểm tra Python trong venv
where python
python --version
```

### Bước 2: Cài Đặt Dependencies
```cmd
# Đảm bảo pip mới nhất
python -m pip install --upgrade pip

# Cài đặt tất cả dependencies
pip install -r requirements.txt

# Nếu lỗi, cài từng cái một:
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install sqlalchemy==2.0.23
pip install pymysql==1.1.0
pip install python-dotenv==1.0.1
```

### Bước 3: Kiểm tra Database
```cmd
# Kiểm tra MySQL đang chạy
net start mysql

# Hoặc kiểm tra services
services.msc
```

### Bước 4: Kiểm tra File .env
```cmd
# Kiểm tra file .env tồn tại
type .env

# Nếu không có, copy từ example
copy .env.example .env
```

### Bước 5: Tạo Database
```sql
-- Kết nối MySQL và tạo database
mysql -u root -p
CREATE DATABASE rehab_v3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

### Bước 6: Chạy Migration
```cmd
python migrate_db.py
```

### Bước 7: Thử Chạy Backend
```cmd
python main.py
```

## 🚨 Lỗi Phổ Biến & Cách Fix

### ❌ `ModuleNotFoundError: No module named 'limiter'`
**Fix:**
```cmd
# Tạo file limiter.py trong thư mục backend
echo from slowapi import Limiter, _rate_limit_exceeded_handler > limiter.py
echo from slowapi.util import get_remote_address >> limiter.py
echo. >> limiter.py
echo limiter = Limiter(key_func=get_remote_address) >> limiter.py
```

### ❌ Database Connection Error
**Fix:**
1. Kiểm tra MySQL đang chạy: `net start mysql`
2. Kiểm tra thông tin kết nối trong `.env`
3. Tạo database: `CREATE DATABASE rehab_v3;`

### ❌ `ImportError: cannot import name 'init_db'`
**Fix:**
```cmd
# Kiểm tra file models/__init__.py tồn tại
dir models\__init__.py

# Nếu không có, tạo file trống
echo. > models\__init__.py
```

### ❌ Port 8000 already in use
**Fix:**
```cmd
# Tìm process đang dùng port
netstat -ano | findstr :8000

# Kill process (thay PID_NUMBER bằng số thật)
taskkill /PID PID_NUMBER /F
```

## 🏃‍♂️ Script Chạy Nhanh

**Tạo file `fix-backend.bat`:**
```batch
@echo off
echo === Fixing Backend Issues ===

cd backend

echo 1. Activating virtual environment...
call venv\Scripts\activate

echo 2. Upgrading pip...
python -m pip install --upgrade pip

echo 3. Installing requirements...
pip install -r requirements.txt

echo 4. Checking database...
python migrate_db.py

echo 5. Starting backend...
python main.py

pause
```

**Lưu script này và chạy:** `fix-backend.bat`

## 📋 Checklist Trước Khi Chạy

- [ ] Python 3.10+ đã cài đặt
- [ ] MySQL Server đang chạy
- [ ] Virtual environment đã được tạo và kích hoạt
- [ ] Dependencies đã được cài đặt
- [ ] File `.env` đã được cấu hình đúng
- [ ] Database `rehab_v3` đã được tạo
- [ ] Migration đã chạy thành công

## 🆘 Nếu Vẫn Lỗi

**Gửi thông tin sau để được hỗ trợ:**

1. **Screenshot lỗi** từ terminal
2. **Version info:**
   ```cmd
   python --version
   pip --version
   mysql --version
   ```
3. **Logs chi tiết:** Copy toàn bộ error message