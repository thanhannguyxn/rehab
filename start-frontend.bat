@echo off
setlocal
echo ================================
echo Starting Frontend Server...
echo ================================
echo.

cd /d %~dp0frontend

if not exist .env (
	if exist .env.example (
		copy /Y .env.example .env >nul
		echo [INFO] Created frontend/.env from .env.example
	) else (
		echo [WARNING] frontend/.env.example not found.
	)
)

if not exist node_modules (
	if exist package-lock.json (
		echo [INFO] Installing dependencies with npm ci...
		call npm ci
	) else (
		echo [INFO] Installing dependencies with npm install...
		call npm install
	)
)

call npm run dev

pause
