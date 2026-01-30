@echo off
chcp 65001 >nul
title Auto GitHub Setup - AI BET Platform

echo 🚀 АВТОМАТИЧЕСКАЯ НАСТРОЙКА GITHUB
echo =====================================
echo.
echo ⚡ Это настроит GitHub БЕЗ запросов пароля!
echo ⏰ Примерное время: 30 секунд
echo.

REM Проверяем Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo Установите Python 3.8+ и повторите
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Запускаем автоматическую настройку
python auto_github_setup.py

echo.
echo 🎉 Готово! Теперь используйте:
echo    gp - быстрый push
echo    ga - быстрый add  
echo    gc - быстрый commit
echo    auto - автопуш
echo.
echo Больше никаких запросов пароля! 🔓
pause
