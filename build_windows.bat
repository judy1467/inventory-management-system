@echo off
chcp 65001 >nul
echo ====================================
echo IMS 재고관리 - Windows 빌드 스크립트
echo ====================================
echo.
echo [1/4] 가상환경 확인...
if exist venv\Scripts\python.exe (
    echo     가상환경이 존재합니다.
) else (
    echo     가상환경을 생성합니다...
    python -m venv venv
)

echo.
echo [2/4] 가상환경 활성화 및 패키지 설치...
call venv\Scripts\activate.bat
python -m pip install -U pip
pip install PySide6 pyinstaller
pip install -r requirements.txt 2>nul

echo.
echo [3/4] 빌드 시작...
pyinstaller --clean 재고관리_windows.spec

echo.
echo [4/4] 빌드 완료!
echo     출력 폴더: dist\IMS_재고관리\
echo     실행 파일: dist\IMS_재고관리\IMS_재고관리.exe
echo.
echo ====================================
pause
