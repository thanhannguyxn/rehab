# HƯỚNG DẪN SETUP HOÀN CHỈNH - REHAB V3

## TỔNG QUAN

Project này gồm 2 phần:
1. **Backend** - FastAPI + MediaPipe + SQLite
2. **Frontend** - React + TypeScript + Tailwind

## YÊU CẦU HỆ THỐNG

- Python 3.8+
- Node.js 18+
- npm hoặc yarn
- Camera (webcam)
- Browser hiện đại (Chrome/Edge/Firefox)

---

## PHẦN 1: SETUP BACKEND

### Bước 1: Tạo thư mục và file backend

```bash
# Tạo thư mục
mkdir -p rehab-v3/backend
cd rehab-v3/backend

# Copy file backend_v3_complete.py vào đây
# Đổi tên thành main.py
cp /path/to/backend_v3_complete.py main.py
```

### Bước 2: Tạo Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài Dependencies

```bash
pip install fastapi uvicorn[standard] websockets opencv-python mediapipe numpy pyjwt
```

Hoặc tạo file `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
opencv-python==4.8.1.78
mediapipe==0.10.8
numpy==1.24.3
pyjwt==2.8.0
```

Rồi cài:
```bash
pip install -r requirements.txt
```

### Bước 4: Chạy Backend

```bash
python main.py
```

**Kết quả:**
```
============================================================
Rehab System V3 - Full Features
============================================================
Server: http://localhost:8000
Docs: http://localhost:8000/docs

Default Accounts:
   Doctor: doctor1 / doctor123
   Patient: patient1 / patient123
============================================================
```

### Bước 5: Test Backend

Mở browser: http://localhost:8000/docs

Test API Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"patient1","password":"patient123"}'
```

---

## PHẦN 2: SETUP FRONTEND

### Bước 1: Di chuyển folder frontend

```bash
# Giả sử frontend đã được tạo tại rehab-v3-frontend
cd rehab-v3-frontend
```

### Bước 2: Cài Dependencies

```bash
npm install
```

**Dependencies sẽ được cài:**
- react, react-dom, react-router-dom
- axios
- recharts (charts)
- jspdf, jspdf-autotable (PDF)
- lucide-react (icons)
- tailwindcss, postcss, autoprefixer
- vite, typescript

### Bước 3: Verify Structure

Đảm bảo structure như sau:
```
rehab-v3-frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── context/
│   ├── hooks/
│   ├── utils/
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### Bước 4: Chạy Frontend

```bash
npm run dev
```

**Kết quả:**
```
VITE v5.0.8  ready in 500 ms

Local:   http://localhost:5173/
Network: use --host to expose
```

### Bước 5: Mở Browser

Truy cập: http://localhost:5173

Bạn sẽ thấy trang Login!

---

## PHẦN 3: TEST TOÀN BỘ HỆ THỐNG

### Test 1: Login Bệnh Nhân

1. Mở http://localhost:5173
2. Nhập:
   - Username: `patient1`
   - Password: `patient123`
3. Click "Đăng Nhập"
4. Bạn sẽ thấy Patient Dashboard

### Test 2: Tập Luyện

1. Click "Bắt Đầu Tập Luyện"
2. Chọn bài tập (Nâng Tay hoặc Squat)
3. Click "Bắt Đầu Tập"
4. Cho phép camera access
5. Đứng trước camera
6. Làm bài tập và xem AI tracking!

### Test 3: Xem Lịch Sử

1. Sau khi tập xong, click "Xem Lịch Sử"
2. Xem biểu đồ tiến bộ
3. Xem các buổi tập trước

### Test 4: Login Bác Sĩ

1. Logout
2. Login với:
   - Username: `doctor1`
   - Password: `doctor123`
3. Xem danh sách bệnh nhân
4. Click vào patient1
5. Xem chi tiết, biểu đồ
6. Click "Tải PDF" để download báo cáo

---

## TROUBLESHOOTING

### Backend Issues

**Port 8000 bị chiếm:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Import error:**
```bash
pip install --upgrade pip setuptools
pip install mediapipe opencv-python
```

**Database error:**
- Xóa file `rehab_v3.db`
- Restart backend (auto recreate)

### Frontend Issues

**npm install fails:**
```bash
# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Port 5173 bị chiếm:**
- Edit `vite.config.ts`, đổi port:
```typescript
server: {
  port: 3000, // Đổi port khác
  // ...
}
```

**WebSocket không connect:**
- Verify backend đang chạy
- Check console errors
- Đảm bảo CORS đúng trong backend

### Camera Issues

**Camera không hoạt động:**
- Kiểm tra quyền camera
- Thử browser khác (Chrome recommended)
- Đảm bảo dùng localhost hoặc HTTPS

**Skeleton không hiện:**
- Kiểm tra lighting tốt
- Đứng cách camera 2-3m
- Đảm bảo toàn thân trong frame

---

## DEPLOYMENT

### Backend Deployment

**Option 1: Local Server**
```bash
# Run with nohup
nohup python main.py > backend.log 2>&1 &
```

**Option 2: Docker**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Frontend Deployment

**Build for production:**
```bash
npm run build
```

**Deploy to:**
- Vercel: `vercel deploy`
- Netlify: Drag & drop `dist/` folder
- Apache/Nginx: Copy `dist/` to web root

**Important:** Update API URLs in production!

---

## CHECKLIST HOÀN THÀNH

### Backend
- [ ] Python 3.8+ installed
- [ ] Virtual env created
- [ ] Dependencies installed
- [ ] Backend running on port 8000
- [ ] Can access http://localhost:8000/docs
- [ ] Database created (rehab_v3.db)
- [ ] Default accounts working

### Frontend
- [ ] Node.js 18+ installed
- [ ] Dependencies installed
- [ ] Frontend running on port 5173
- [ ] Can access login page
- [ ] Can login successfully
- [ ] Camera access granted
- [ ] WebSocket connects
- [ ] Can do exercise
- [ ] Charts display correctly

### Integration
- [ ] Patient can login and exercise
- [ ] Session saves to database
- [ ] Patient can view history
- [ ] Doctor can login
- [ ] Doctor can see patients
- [ ] Doctor can view patient details
- [ ] PDF export works

---

## SUPPORT COMMANDS

### Start Everything (Full Stack)

**Terminal 1 - Backend:**
```bash
cd rehab-v3/backend
source venv/bin/activate  # hoặc venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd rehab-v3-frontend
npm run dev
```

### Stop Everything

- Ctrl+C trong mỗi terminal
- Hoặc close terminal windows

### Clean Restart

**Backend:**
```bash
rm rehab_v3.db  # Delete database
python main.py   # Recreate with defaults
```

**Frontend:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## KẾT QUẢ CUỐI CÙNG

Khi setup thành công, bạn sẽ có:

- Backend API đầy đủ chức năng
- Frontend UI đẹp, senior-friendly
- Real-time pose tracking với MediaPipe
- Session management với database
- Patient dashboard với charts
- Doctor dashboard với analytics
- PDF report generation
- Full authentication system

---

## NEXT STEPS

1. Thêm exercise types mới
2. Customize UI colors
3. Add more patients/doctors
4. Improve error detection
5. Add video recording
6. Deploy to production

