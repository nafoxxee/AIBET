@echo off
chcp 65001 >nul
echo 🚀 Permanente GitHub Setup for AI BET Platform
echo ================================================

REM Проверяем Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден! Установите Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Запускаем скрипт настройки
python setup_github_permanent.py

echo.
echo 🎉 Настройка завершена!
pause
