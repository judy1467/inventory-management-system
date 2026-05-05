# Windows Build Instructions

## Requirements

- **Python 3.8 or higher** from [python.org](https://www.python.org/downloads/)
- Windows 10 or later

## Quick Start

1. **Double-click** `build_windows.bat`
2. Wait for the build to complete
3. Run `dist\IMS_Inventory\IMS_Inventory.exe`

That's it!

## What the build script does

1. Cleans old build files (venv, build, dist folders)
2. Creates a fresh virtual environment
3. Installs PySide6 and PyInstaller
4. Builds a standalone Windows executable
5. Copies existing CSV data files (if any)

## Output

```
dist/
└── IMS_Inventory/
    ├── IMS_Inventory.exe    ← Double-click to run
    ├── inventory.csv        ← Created on first run
    ├── transactions.csv     ← Created on first run
    └── [various DLL files]
```

## Troubleshooting

### "WARNING: Cache entry deserialization failed"

This is a pip cache issue (usually from mixing Python versions).
The build script already uses `--no-cache-dir` to avoid this.

If you still see this warning, you can manually clear the pip cache:
```batch
python -m pip cache purge
```
The warning is harmless - the build will complete successfully.

### "Python not found in PATH"

Install Python from https://www.python.org/downloads/
During installation, **check the box** "Add Python to PATH"

### Build succeeds but .exe crashes

This is usually a missing system DLL. Install:
- **Visual C++ Redistributable**: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Antivirus blocks the .exe

PyInstaller executables sometimes trigger false positives.
Add `dist\IMS_Inventory\` to your antivirus exceptions.

## Manual Build (Advanced)

If the batch script doesn't work, build manually:

```batch
REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
pip install PySide6 pyinstaller

REM Build
pyinstaller --name=IMS_Inventory --windowed --onedir ims_inventory.py

REM Run
dist\IMS_Inventory\IMS_Inventory.exe
```

## Anaconda Users

If you have Anaconda installed, the build might encounter DLL conflicts.

**Solution**: Install official Python from python.org alongside Anaconda.
Both can coexist. The build script will use whichever is in PATH.
