@echo off
cls
echo ===========================================
echo IMS Inventory System - Windows Build
echo ===========================================
echo.

python --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo [Step 1/4] Creating virtual environment...
if not exist venv\Scripts\python.exe (
    python -m venv venv
)

echo.
echo [Step 2/4] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install -U pip
pip install PySide6 pyinstaller

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
pyinstaller --clean inventory_windows.spec

echo.
echo ===========================================
if exist dist\IMS_Inventory\IMS_Inventory.exe (
    echo BUILD SUCCESS
    echo Output folder: dist\IMS_Inventory\
) else (
    echo BUILD FAILED - check errors above
)
echo ===========================================
pause
