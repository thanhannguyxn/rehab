@echo off
setlocal
echo ================================
echo Starting Backend Server...
echo ================================
echo.

cd /d %~dp0backend

if not exist venv (
	echo [INFO] Creating backend virtual environment...
	python -m venv venv
)

call venv\Scripts\activate.bat

if not exist .env (
	if exist .env.example (
		copy /Y .env.example .env >nul
		echo [INFO] Created backend/.env from .env.example
	) else (
		echo [ERROR] Missing backend/.env and backend/.env.example.
		pause
		exit /b 1
	)
)

echo [INFO] Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
	echo [ERROR] Failed to install backend dependencies.
	pause
	exit /b 1
)

echo [INFO] Running database migration...
python migrate_db.py
if errorlevel 1 (
	echo [WARNING] Migration failed. Check MySQL service and backend/.env.
)

python main.py

pause
