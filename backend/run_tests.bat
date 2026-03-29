@echo off
cd /d "C:\Users\Admin\Documents\rehab-system\capstone-project-a-hn2-2\backend"
python -m pytest --cov=. --cov-report=term-missing
pause
