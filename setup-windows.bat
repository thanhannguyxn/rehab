@echo off
setlocal
echo ====================================
echo Rehab System V3 - Setup for Windows
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Setting up Backend...
cd /d %~dp0backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies.
    pause
    exit /b 1
)

if not exist .env (
    if exist .env.example (
        copy /Y .env.example .env >nul
        echo Created backend/.env from .env.example
    ) else (
        echo WARNING: backend/.env.example not found. Please create backend/.env manually.
    )
)

echo.
echo [2/4] Setting up Frontend...
cd /d %~dp0frontend

if exist package-lock.json (
    echo Installing Node.js dependencies with npm ci...
    call npm ci
) else (
    echo Installing Node.js dependencies with npm install...
    call npm install
)
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies.
    pause
    exit /b 1
)

if not exist .env (
    if exist .env.example (
        copy /Y .env.example .env >nul
        echo Created frontend/.env from .env.example
    ) else (
        echo WARNING: frontend/.env.example not found. Please create frontend/.env manually.
    )
)

echo.
echo [3/4] Setup Summary
echo - backend/.env: ready
echo - frontend/.env: ready
echo.
echo [4/4] Done
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To start the application:
echo 1. Run "start-backend.bat" in one terminal
echo 2. Run "start-frontend.bat" in another terminal
echo 3. Open http://localhost:3000 in your browser
echo.
echo Default accounts:
echo   Doctor:  doctor1 / doctor123
echo   Patient: patient1 / patient123
echo.
pause
