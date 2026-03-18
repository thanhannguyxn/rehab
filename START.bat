@echo off
setlocal
echo ============================================================
echo   HE THONG PHUC HOI CHUC NANG V3 - QUICK START
echo ============================================================
echo.

echo [1/2] Starting Backend...
start cmd /k "cd /d %~dp0 && call start-backend.bat"
timeout /t 5

echo.
echo [2/2] Starting Frontend...
start cmd /k "cd /d %~dp0 && call start-frontend.bat"

echo.
echo ============================================================
echo   HOAN THANH!
echo ============================================================
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Tai khoan:
echo   - Bac si: doctor1 / doctor123
echo   - Benh nhan: patient1 / patient123
echo ============================================================
pause
