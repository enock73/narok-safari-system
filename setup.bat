@echo off
:: ═══════════════════════════════════════════════════════════════
::  MaraGate System — Windows Setup Script
::  Run this ONCE to install dependencies and initialise the DB
:: ═══════════════════════════════════════════════════════════════

title MaraGate Setup

echo.
echo  ============================================================
echo   MaraGate — Maasai Mara Ecosystem Management System
echo   Narok County Government
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo          Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [1/5] Python detected.

:: Check pip
pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo  [ERROR] pip not found. Reinstall Python with pip.
    pause
    exit /b 1
)

:: Create virtual environment
echo  [2/5] Creating virtual environment...
IF NOT EXIST "venv" (
    python -m venv venv
    echo        Done.
) ELSE (
    echo        Already exists.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo  [3/5] Installing Python packages...
pip install -r requirements.txt --quiet
IF ERRORLEVEL 1 (
    echo  [ERROR] Package installation failed. Check requirements.txt.
    pause
    exit /b 1
)
echo        Done.

:: Create .env if not present
echo  [4/5] Setting up environment file...
IF NOT EXIST ".env" (
    copy .env.example .env
    echo        Created .env from .env.example
    echo        [!] Edit .env and set your DB_PASSWORD before continuing.
    echo.
    echo        Press any key after editing .env ...
    pause >nul
) ELSE (
    echo        .env already exists.
)

:: Initialize database
echo  [5/5] Initialising database...
python init_db.py
IF ERRORLEVEL 1 (
    echo  [ERROR] Database init failed. Check MySQL is running and credentials in .env
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   Setup Complete!
echo.
echo   Run the application with:
echo     run_app.bat
echo.
echo   Or manually:
echo     venv\Scripts\activate
echo     python run.py
echo  ============================================================
echo.
pause
