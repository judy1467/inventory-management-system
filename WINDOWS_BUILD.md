# Windows Build Guide - Official Python Required

## ⚠️ IMPORTANT: Use Official Python ONLY

This project **requires official Python from python.org**.  
**DO NOT use Anaconda Python** - it causes DLL conflicts with PyInstaller.

## Why Not Anaconda?

Anaconda Python includes its own DLLs (libcrypto, libssl, liblzma, etc.) that conflict with PyInstaller's bundling process. This causes errors like:

```
WARNING: Library not found: could not resolve 'libcrypto-3-x64.dll'
ImportError: DLL load failed while importing QtCore
```

## Installation Steps

### 1. Download Official Python

- Go to https://www.python.org/downloads/
- Download **Python 3.10, 3.11, or 3.12** (64-bit)
- Run the installer

### 2. During Installation

**IMPORTANT:** Check these options:
- ☑ **Add Python to PATH**
- ☑ Install for all users (optional but recommended)

### 3. Verify Installation

Open Command Prompt and run:
```batch
py --version
```

Should show something like: `Python 3.11.x` or `Python 3.12.x`

### 4. Build the Application

Simply double-click `build_windows.bat` or run:
```batch
build_windows.bat
```

The script will:
- ✅ Automatically find official Python
- ✅ Reject Anaconda Python if found
- ✅ Create a clean virtual environment
- ✅ Install PySide6 and PyInstaller
- ✅ Build the executable

## Output

After successful build:
```
dist\IMS_Inventory\IMS_Inventory.exe  ← Your application
```

## Can I Keep Anaconda Installed?

**Yes!** You can have both Anaconda and official Python installed on the same computer. They won't conflict. The build script will automatically choose official Python.

## Troubleshooting

### "Official Python NOT found" error

The script couldn't find official Python. Make sure you:
1. Downloaded from python.org (NOT Anaconda)
2. Checked "Add Python to PATH" during installation
3. Restarted Command Prompt after installation

### Build succeeds but exe crashes on startup

Check if you accidentally used Anaconda Python. Delete these folders and rebuild:
```batch
rmdir /s /q venv
rmdir /s /q build
rmdir /s /q dist
build_windows.bat
```

### "vcruntime140.dll not found" error when running exe

Install Microsoft Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe
