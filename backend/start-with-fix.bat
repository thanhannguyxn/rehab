@echo off
echo ======================================
echo FIX VA KHOI DONG HE THONG
echo ======================================

cd /d "%~dp0backend"

echo [1/5] Activating virtual environment...
call venv\Scripts\activate

echo [2/5] Installing/Upgrading dependencies...
pip install -r requirements.txt

echo [3/5] Checking database migration...
python migrate_db.py

echo [4/5] Testing services...
python -c "from services.face_service import face_service; from services.pose_service import pose; print('All services OK!')"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Services failed to load!
    pause
    exit /b 1
)

echo [5/5] Starting backend server...
python main.py

pause
