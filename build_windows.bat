@echo off
setlocal EnableDelayedExpansion
cls
echo ===========================================
echo IMS Inventory System - Windows Build
echo ===========================================
echo.

set PYTHON_CMD=

REM Try python, python3, py in order
for %%C in (python python3 py) do (
    %%C --version >nul 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD=%%C
        goto :found_python
    )
)

echo ERROR: Python not found.
echo Please install Python from https://python.org
echo During installation, CHECK "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo Python found: !PYTHON_CMD!
!PYTHON_CMD! --version

echo.
echo [Step 1/3] Creating virtual environment...
if not exist venv\Scripts\python.exe (
    !PYTHON_CMD! -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Try running as Administrator.
        pause
        exit /b 1
    )
)

echo.
echo [Step 2/3] Installing dependencies...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install -U pip
venv\Scripts\pip.exe install PySide6 pyinstaller

echo.
echo [Step 3/3] Building executable...
venv\Scripts\pyinstaller.exe --clean inventory_windows.spec

echo.
echo ===========================================
if exist dist\IMS_Inventory\IMS_Inventory.exe (
    echo BUILD SUCCESS
    echo Output: dist\IMS_Inventory\
    echo.
    echo NOTE: Data files (재고목록.csv, 입출고기록.csv)
    echo       are created automatically on first run.
    echo       If you have existing data, copy those CSV files
    echo       into the dist\IMS_Inventory\ folder.
) else (
    echo BUILD FAILED - see errors above
)
echo ===========================================
pause
endlocal
