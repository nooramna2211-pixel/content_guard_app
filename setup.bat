@echo off
setlocal
title Content Guard Setup
cd /d "%~dp0"

echo.
echo  ========================================
echo       Content Guard - Windows Setup
echo  ========================================

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 installer.py setup
    if errorlevel 1 goto :failed
    goto :success
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python installer.py setup
    if errorlevel 1 goto :failed
    goto :success
)

echo [ERROR] Python 3 was not found. Install Python 3.10 or newer and try again.
goto :failed

:success
echo.
echo Setup finished successfully.
pause
exit /b 0

:failed
echo.
echo Setup did not finish. Review the message above and try again.
pause
exit /b 1
