@echo off
:: ══════════════════════════════════════════════
::  MaraGate — Start Application (Windows)
:: ══════════════════════════════════════════════

title MaraGate — Running

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo  ============================================================
echo   MaraGate System is starting...
echo   Open your browser at: http://localhost:5000
echo   Press Ctrl+C to stop.
echo  ============================================================
echo.

set FLASK_APP=run.py
set FLASK_ENV=development

python run.py

pause
