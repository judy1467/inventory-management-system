# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows executable build
# Works with both official Python and Anaconda (with warnings)

import os
import sys

# Check if running from Anaconda (warn but don't block)
conda_meta_exists = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
is_anaconda = conda_meta_exists or 'anaconda' in sys.version.lower()

if is_anaconda:
    print("=" * 60)
    print("WARNING: Building with Anaconda Python")
    print(f"Python: {sys.executable}")
    print()
    print("This may cause DLL conflicts. If the build fails,")
    print("install official Python from https://python.org")
    print("=" * 60)
    print()

block_cipher = None

# Bundle data files if they exist
datas = []
for data_file in ["inventory.csv", "transactions.csv"]:
    if os.path.exists(data_file):
        datas.append((data_file, "."))

# If using Anaconda, try to bundle common missing DLLs
binaries = []
if is_anaconda and sys.platform == 'win32':
    print("Attempting to locate Anaconda DLLs...")
    anaconda_dll_dirs = [
        os.path.join(sys.prefix, 'Library', 'bin'),
        os.path.join(sys.prefix, 'DLLs'),
    ]
    
    required_dlls = [
        'libcrypto-3-x64.dll',
        'libssl-3-x64.dll', 
        'liblzma.dll',
        'libbz2.dll',
    ]
    
    for dll_dir in anaconda_dll_dirs:
        if os.path.exists(dll_dir):
            for dll_name in required_dlls:
                dll_path = os.path.join(dll_dir, dll_name)
                if os.path.exists(dll_path):
                    binaries.append((dll_path, '.'))
                    print(f"  Found: {dll_name}")

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
