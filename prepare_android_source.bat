@echo off
setlocal
title Prepare Content Guard Android Sources
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 prepare_android_source.py
    if errorlevel 1 goto :failed
    goto :success
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python prepare_android_source.py
    if errorlevel 1 goto :failed
    goto :success
)

echo [ERROR] Python 3 was not found.
goto :failed

:success
echo.
echo Upload dist\ContentGuard-Android-Source.zip in colab_build_android.ipynb.
pause
exit /b 0

:failed
echo.
echo Could not prepare the Android source archive.
pause
exit /b 1
