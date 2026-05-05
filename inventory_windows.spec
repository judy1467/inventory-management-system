# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows executable build
# REQUIRES: Official Python from python.org (NOT Anaconda)
# Run: pyinstaller --clean inventory_windows.spec

import os
import sys

# Verify we're NOT running from Anaconda
if 'conda' in sys.executable.lower() or 'anaconda' in sys.executable.lower():
    print("=" * 60)
    print("ERROR: Anaconda Python detected!")
    print(f"Current Python: {sys.executable}")
    print()
    print("This build MUST use official Python from python.org")
    print("to avoid DLL conflicts.")
    print()
    print("Please:")
    print("1. Install official Python from https://python.org")
    print("2. Run build_windows.bat (it will find official Python)")
    print("=" * 60)
    sys.exit(1)

block_cipher = None

# Bundle data files if they exist
datas = []
for data_file in ["inventory.csv", "transactions.csv"]:
    if os.path.exists(data_file):
        datas.append((data_file, "."))

# NO binaries from Anaconda - let PyInstaller handle everything automatically
binaries = []

a = Analysis(
    ["ims_inventory.py"],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Explicitly exclude Anaconda packages
        "conda",
        "anaconda_navigator",
        "_anaconda_numpy_init",
    ],
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
