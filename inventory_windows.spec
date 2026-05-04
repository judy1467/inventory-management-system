# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows executable build
# Run: pyinstaller --clean inventory_windows.spec

import os

block_cipher = None

# Only bundle data files that actually exist.
# App creates CSVs automatically on first run if missing.
datas = []
for data_file in ['재고목록.csv', '입출고기록.csv']:
    if os.path.exists(data_file):
        datas.append((data_file, '.'))

a = Analysis(
    ['ims_inventory.py'],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=datas,
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
    name='IMS_Inventory',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='IMS_Inventory',
)
