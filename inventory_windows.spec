# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows executable build
# Run: pyinstaller --clean inventory_windows.spec

import os
import sys
import glob

block_cipher = None

# Anaconda DLL fix: 생성된 exe가 Anaconda의 해당 DLL을 찾지 못하는 문제 해결
binaries = []
anaconda_base = getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None)
if anaconda_base:
    for subdir in ["Library/bin", "DLLs"]:
        dll_dir = os.path.join(anaconda_base, subdir)
        if os.path.isdir(dll_dir):
            for dll in glob.glob(os.path.join(dll_dir, "*.dll")):
                binaries.append((dll, "."))

a = Analysis(
    ["ims_inventory.py"],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=binaries,
    datas=[],
    hiddenimports=[
        "ssl",
        "_ssl",
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
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
    name="IMS_Inventory",
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
    name="IMS_Inventory",
)
