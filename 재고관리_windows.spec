# -*- mode: python ; coding: utf-8 -*-

import os

# Windows 실행파일 빌드용 PyInstaller spec
# 빌드 명령어: pyinstaller 재고관리_windows.spec
# 결과물: dist/IMS_재고관리/ 폴더 전체를 배포하세요.

block_cipher = None

a = Analysis(
    ['재고관리_pyside6.py'],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=[
        # CSV 데이터 파일: 빌드 시점에 없으면 주석 처리 or 빈 파일 생성
        ('재고목록.csv', '.'),
        ('입출고기록.csv', '.'),
    ],
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IMS_재고관리',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               # UPX 압축 끔 (Qt 호환성 문제 방지)
    console=False,           # 창용 앱 (콘솔 숨김)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app_icon.ico',   # 아이콘 추가 시 주석 해제
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='IMS_재고관리',
)
