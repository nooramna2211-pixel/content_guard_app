@echo off
setlocal
title Build Content Guard Installer
cd /d "%~dp0"

echo.
echo  ========================================
echo       Content Guard - Windows Build
echo  ========================================

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=py -3"
    goto :python_found
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=python"
    goto :python_found
)
echo [ERROR] Python 3.10 or newer was not found.
goto :failed

:python_found
%PYTHON% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required to build Content Guard.
    goto :failed
)

echo [1/3] Installing application and build dependencies...
%PYTHON% -m pip install -r requirements-build.txt
if errorlevel 1 goto :failed

echo [2/3] Packaging Content Guard...
%PYTHON% -m PyInstaller --noconfirm --clean packaging\content_guard.spec
if errorlevel 1 goto :failed

echo Creating the downloadable Windows ZIP...
%PYTHON% -c "import shutil; shutil.make_archive('dist/ContentGuard-Windows', 'zip', root_dir='dist', base_dir='ContentGuard')"
if errorlevel 1 goto :failed

where ISCC >nul 2>nul
if errorlevel 1 (
    echo.
    echo [NOTICE] Executable and ZIP are ready in dist\ContentGuard and dist\ContentGuard-Windows.zip.
    echo Install Inno Setup 6 and add ISCC.exe to PATH to build the installer.
    goto :success
)

echo [3/3] Building the single-file Windows installer...
ISCC packaging\content_guard.iss
if errorlevel 1 goto :failed

:success
echo.
echo Build completed. See dist\ContentGuard-Windows.zip and the installer output.
pause
exit /b 0

:failed
echo.
echo Build failed. Review the error output above.
pause
exit /b 1
