@echo off
setlocal
title Content Guard
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Content Guard is not set up yet. Run setup.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" installer.py start
if errorlevel 1 (
    echo.
    echo Could not start Content Guard. Check instance\content_guard.log.
    pause
    exit /b 1
)
exit /b 0
