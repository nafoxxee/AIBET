@echo off
echo Starting AI BET Analytics Platform...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
python -m pip install --user -r requirements.txt

echo.
echo Running basic test...
python test_basic.py

echo.
echo Starting main application...
python app/main.py

pause
