# CamForge Build Guide

> Package CamForge as a standalone Windows .exe application

English | [中文](BUILD.md)

---

## Prerequisites

- **Python 3.10+** (3.13 recommended)
- **pip dependencies**: `pip install -r requirements.txt`
- **PyInstaller**: `pip install pyinstaller`

Optional:
- **UPX**: https://upx.github.io/ — compresses executable size (auto-detected by PyInstaller)

---

## Quick Build

```batch
build.bat
```

The script automatically:
1. Checks and installs PyInstaller
2. Generates the app icon (if missing)
3. Cleans previous build artifacts
4. Runs PyInstaller build → `dist\CamForge.exe`

---

## Manual Build

```batch
python -m PyInstaller CamForge.spec --noconfirm --clean
```

Output: `dist\CamForge.exe` (single file, ~70 MB)

---

## Icon

Run `python make_icon.py` to generate `camforge.ico`. To use a custom icon, replace this file.

---

## Troubleshooting

### 1. matplotlib fonts missing

**Symptom**: Chart text shows as boxes, or error `findfont: Font family ... not found`

**Fix**: Verify `datas=mpl_datas` and `collect_data_files('matplotlib')` in `CamForge.spec`

### 2. tkinter.TclError: Can't find a usable tk.tcl

**Symptom**: Crash on startup with Tcl/Tk error

**Fix**: Check Python installation includes tcl/tk components

### 3. ModuleNotFoundError: No module named 'PIL' / 'openpyxl'

**Symptom**: GIF export or Excel export not available

**Fix**: Verify `hiddenimports` includes `'PIL'`, `'openpyxl'`

### 4. Antivirus / Firewall "Unknown Publisher" warning

**Symptom**: Windows Defender or firewall shows "Unknown publisher" warning

**Fix**:
- Click "More info" → "Run anyway" to proceed
- To eliminate the warning permanently, use a code signing certificate (EV code signing cert gets immediate SmartScreen trust)
- Add the .exe to AV exclusion list

### 5. Slow first startup

**Symptom**: Takes 5-10 seconds after double-clicking the .exe

**Cause**: One-file mode extracts embedded dependencies to a temp directory on first run

**Fix**: Subsequent launches are faster (temp files cached)
