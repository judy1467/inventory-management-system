@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cls
echo ============================================
echo IMS Inventory Management System
echo Windows Build Script
echo ============================================
echo.

REM Clean previous builds
echo Cleaning previous build files...
if exist venv rmdir /s /q venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
echo.

REM Find Python
set PYTHON=
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=python
    goto :found
)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON=py
    goto :found
)

echo ERROR: Python not found in PATH
echo.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:found
echo Found Python: %PYTHON%
%PYTHON% --version
echo.

REM Create virtual environment
echo [1/4] Creating virtual environment...
%PYTHON% -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate and upgrade pip
echo [2/4] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --no-cache-dir --quiet
python -m pip install PySide6 pyinstaller --no-cache-dir --quiet

REM Build executable
echo [3/4] Building executable...
python -m PyInstaller ^
    --name=IMS_Inventory ^
    --windowed ^
    --onedir ^
    --clean ^
    --noconfirm ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

REM Copy data files if they exist
echo [4/4] Copying data files...
if exist inventory.csv copy /y inventory.csv dist\IMS_Inventory\ >nul
if exist transactions.csv copy /y transactions.csv dist\IMS_Inventory\ >nul

echo.
echo ============================================
echo BUILD SUCCESS!
echo ============================================
echo.
echo Executable location:
echo   dist\IMS_Inventory\IMS_Inventory.exe
echo.
echo To run:
echo   cd dist\IMS_Inventory
echo   IMS_Inventory.exe
echo.
echo Data files (inventory.csv, transactions.csv) will be
echo created automatically on first run if they don't exist.
echo.
pause
