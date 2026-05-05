@echo off
setlocal EnableDelayedExpansion
cls
echo ===========================================
echo IMS Inventory System - Windows Build
echo ===========================================
echo.

REM Step 0: Clean old venv to avoid contamination
if exist venv (
    echo [Cleanup] Removing old venv folder...
    rmdir /s /q venv
)
if exist build (
    echo [Cleanup] Removing old build folder...
    rmdir /s /q build
)
if exist dist (
    echo [Cleanup] Removing old dist folder...
    rmdir /s /q dist
)

REM Find ONLY official Python (explicitly avoid Anaconda)
set PYTHON_CMD=
set FOUND_PYTHON=0

echo [Searching] Looking for official Python installation...
echo.

REM Try common official Python installation paths
for %%V in (312 311 310 39 38) do (
    if exist C:\Python%%V\python.exe (
        set PYTHON_CMD=C:\Python%%V\python.exe
        set FOUND_PYTHON=1
        echo Found: C:\Python%%V\python.exe
        goto :check_python
    )
    if exist C:\Program Files\Python%%V\python.exe (
        set PYTHON_CMD=C:\Program Files\Python%%V\python.exe
        set FOUND_PYTHON=1
        echo Found: C:\Program Files\Python%%V\python.exe
        goto :check_python
    )
)

REM Try py launcher with official Python
py --version >nul 2>nul
if not errorlevel 1 (
    REM Check if py points to Anaconda
    py -c "import sys; exit(1 if 'conda' in sys.executable.lower() or 'anaconda' in sys.executable.lower() else 0)" >nul 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD=py
        set FOUND_PYTHON=1
        echo Found: py launcher (official Python)
        goto :check_python
    ) else (
        echo Skipped: py launcher points to Anaconda
    )
)

REM If still not found, show error
if !FOUND_PYTHON!==0 (
    echo.
    echo ==================== ERROR ====================
    echo Official Python NOT found.
    echo.
    echo This build script requires official Python from
    echo https://www.python.org/downloads/
    echo.
    echo DO NOT use Anaconda Python - it causes DLL conflicts.
    echo.
    echo Installation steps:
    echo 1. Download Python 3.10, 3.11, or 3.12 from python.org
    echo 2. During installation, CHECK "Add Python to PATH"
    echo 3. After installation, run this script again
    echo.
    echo If you have Anaconda, you can install official Python
    echo alongside it - they won't conflict.
    echo ===========================================
    pause
    exit /b 1
)

:check_python
REM Verify this is NOT Anaconda
!PYTHON_CMD! -c "import sys; exit(1 if 'conda' in sys.executable.lower() or 'anaconda' in sys.executable.lower() else 0)" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ==================== ERROR ====================
    echo The detected Python is from Anaconda distribution.
    echo Path: !PYTHON_CMD!
    echo.
    echo This build REQUIRES official Python from python.org
    echo because Anaconda causes DLL conflicts with PyInstaller.
    echo.
    echo Please install official Python and run this script again.
    echo ===========================================
    pause
    exit /b 1
)

echo.
echo Selected Python: !PYTHON_CMD!
!PYTHON_CMD! --version
echo.

echo [Step 1/3] Creating clean virtual environment...
!PYTHON_CMD! -m venv venv --clear
if errorlevel 1 (
    echo Failed to create venv.
    pause
    exit /b 1
)

echo.
echo [Step 2/3] Installing dependencies in isolated venv...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-cache-dir PySide6 pyinstaller

echo.
echo [Step 3/3] Building executable...
python -m PyInstaller --clean inventory_windows.spec

echo.
echo ===========================================
if exist dist\IMS_Inventory\IMS_Inventory.exe (
    echo BUILD SUCCESS
    echo Output: dist\IMS_Inventory\
    echo.
    echo NOTE: Data files (inventory.csv, transactions.csv)
    echo       are created automatically on first run.
    echo       If you have existing data, copy those CSV files
    echo       into the dist\IMS_Inventory\ folder.
) else (
    echo BUILD FAILED - see errors above
)
echo ===========================================
pause
endlocal
