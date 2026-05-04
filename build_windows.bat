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
echo.
echo Please install Python from https://python.org
echo During installation, CHECK "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo Python found: !PYTHON_CMD!
!PYTHON_CMD! --version

echo.
echo [Step 1/4] Creating virtual environment...
if not exist venv\Scripts\python.exe (
    !PYTHON_CMD! -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Try running as Administrator.
        pause
        exit /b 1
    )
)

echo.
echo [Step 2/4] Installing dependencies...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install -U pip
venv\Scripts\pip.exe install PySide6 pyinstaller

echo.
echo [Step 3/4] Preparing data files...
if not exist stock.csv (
    echo Creating empty stock.csv...
    type nul > stock.csv
)
if not exist history.csv (
    echo Creating empty history.csv...
    type nul > history.csv
)

echo.
echo [Step 4/4] Building executable...
venv\Scripts\pyinstaller.exe --clean inventory_windows.spec

echo.
echo ===========================================
if exist dist\IMS_Inventory\IMS_Inventory.exe (
    echo BUILD SUCCESS
    echo Output: dist\IMS_Inventory\
) else (
    echo BUILD FAILED - see errors above
)
echo ===========================================
pause
endlocal
