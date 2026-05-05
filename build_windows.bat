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

REM Find Python (prefer official Python)
set PYTHON_CMD=
set FOUND_PYTHON=0

echo [Searching] Looking for Python installation...
echo.

REM Try common official Python installation paths
for %%V in (312 311 310 39 38) do (
    if exist C:\Python%%V\python.exe (
        set PYTHON_CMD=C:\Python%%V\python.exe
        set FOUND_PYTHON=1
        echo Found: C:\Python%%V\python.exe
        goto :check_python
    )
    if exist "C:\Program Files\Python%%V\python.exe" (
        set PYTHON_CMD=C:\Program Files\Python%%V\python.exe
        set FOUND_PYTHON=1
        echo Found: C:\Program Files\Python%%V\python.exe
        goto :check_python
    )
)

REM Try py launcher
py --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=py
    set FOUND_PYTHON=1
    echo Found: py launcher
    goto :check_python
)

REM Try python in PATH
python --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python
    set FOUND_PYTHON=1
    echo Found: python in PATH
    goto :check_python
)

REM If still not found, show error
if !FOUND_PYTHON!==0 (
    echo.
    echo ==================== ERROR ====================
    echo Python NOT found.
    echo.
    echo Please install Python from https://python.org
    echo During installation, CHECK "Add Python to PATH"
    echo.
    echo After installation, run this script again.
    echo ===========================================
    pause
    exit /b 1
)

:check_python
REM Verify this is NOT Anaconda (more accurate check)
!PYTHON_CMD! -c "import sys, os; conda_check = os.path.exists(os.path.join(sys.prefix, 'conda-meta')) or 'anaconda' in sys.version.lower(); exit(1 if conda_check else 0)" >nul 2>nul
if errorlevel 1 (
    echo.
    echo ==================== WARNING ====================
    echo The detected Python is from Anaconda distribution.
    !PYTHON_CMD! -c "import sys; print('Path:', sys.executable)"
    !PYTHON_CMD! --version
    echo.
    echo Anaconda Python may cause DLL conflicts with PyInstaller.
    echo.
    echo RECOMMENDED: Install official Python from python.org
    echo and run this script again. You can keep Anaconda installed.
    echo.
    echo Press Ctrl+C to abort, or any key to continue anyway...
    echo ===========================================
    pause >nul
    echo.
    echo Continuing with Anaconda Python (may encounter issues)...
)

echo.
echo Selected Python: !PYTHON_CMD!
!PYTHON_CMD! --version
!PYTHON_CMD! -c "import sys; print('Location:', sys.executable)"
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
    echo To test the executable:
    echo   cd dist\IMS_Inventory
    echo   IMS_Inventory.exe
    echo.
    echo NOTE: Data files (inventory.csv, transactions.csv)
    echo       are created automatically on first run.
) else (
    echo BUILD FAILED - see errors above
    echo.
    echo If you see DLL errors, try installing official Python
    echo from https://python.org and run this script again.
)
echo ===========================================
pause
endlocal
