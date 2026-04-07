@echo off
echo ======================================
echo KHOI CHAY HE THONG AI REHAB
echo ======================================

cd /d "%~dp0"

echo [1/3] Checking backend environment...
cd backend
if not exist venv\ (
    echo Virtual environment not found! Creating...
    python -m venv venv
)

echo [2/3] Starting Backend Server...
start "Rehab Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python main.py"

echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo [3/3] Starting Frontend Server...
cd ..\frontend
start "Rehab Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ======================================
echo HE THONG DANG CHAY!
echo ======================================
echo Backend: http://localhost:8000/docs
echo Frontend: Se tu dong chon port (3000, 3001, hoac 3002)
echo.
echo Xem 2 cua so terminal de biet port cu the!
echo ======================================
pause
