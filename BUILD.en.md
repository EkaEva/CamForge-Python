# CamForge Build Guide

> Package CamForge as a standalone Windows .exe application

English | [中文](BUILD.md)

---

## Prerequisites

- **Python 3.10+** (3.13 recommended)
- **pip dependencies**: `pip install -r requirements.txt`
- **Packaging tools**: `pip install pyinstaller nuitka`

Optional:
- **UPX**: https://upx.github.io/ — compresses executable size (auto-detected by PyInstaller)
- **C compiler**: Nuitka requires MSVC (Visual Studio Build Tools) or MinGW64

---

## Quick Build

```batch
build.bat
```

The script automatically:
1. Checks and installs PyInstaller / Nuitka
2. Generates the app icon (if missing)
3. Cleans previous build artifacts
4. Runs PyInstaller build → `dist\CamForge.exe`
5. Runs Nuitka build → `dist\CamForge_nuitka.exe`

---

## Individual Builds

### PyInstaller

```batch
python -m PyInstaller CamForge.spec --noconfirm --clean
```

Output: `dist\CamForge.exe` (single file, ~80-120 MB)

### Nuitka

```batch
python -c "import matplotlib, os; print(os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data'))" > mpl_data_path.txt
set /p MPL_DATA=<mpl_data_path.txt

python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --windows-icon-from-ico=camforge.ico ^
    --output-filename=CamForge.exe ^
    --output-dir=dist_nuitka ^
    --enable-plugin=tk-inter ^
    --enable-plugin=numpy ^
    --enable-plugin=matplotlib ^
    --include-module=PIL ^
    --include-module=openpyxl ^
    --include-data-dir="%MPL_DATA%=matplotlib/mpl-data" ^
    main.py
```

Output: `dist_nuitka\CamForge.exe` (single file, ~70-100 MB)

---

## Build Outputs

| File | Tool | Size | Startup Speed |
|------|------|------|---------------|
| `dist\CamForge.exe` | PyInstaller | ~80-120 MB | First run ~5-10s (extracts to temp dir) |
| `dist\CamForge_nuitka.exe` | Nuitka | ~70-100 MB | First run ~5-10s (extracts to temp dir) |

> One-file mode has slower first startup because dependencies must be extracted to a temporary directory. Subsequent launches are faster (temp files cached).
> For instant startup, use one-folder mode (remove `--onefile`), which produces a folder with multiple files.

---

## Icon

Run `python make_icon.py` to generate `camforge.ico`. To use a custom icon, replace this file.

---

## Troubleshooting

### 1. matplotlib fonts missing

**Symptom**: Chart text shows as boxes, or error `findfont: Font family ... not found`

**Cause**: matplotlib data files (fonts, stylesheets) not bundled

**Fix**:
- PyInstaller: Verify `datas=mpl_datas` and `collect_data_files('matplotlib')` in `CamForge.spec`
- Nuitka: Verify `--include-data-dir=...=matplotlib/mpl-data` path is correct

### 2. tkinter.TclError: Can't find a usable tk.tcl

**Symptom**: Crash on startup with Tcl/Tk error

**Cause**: TCL/TK libraries not bundled

**Fix**:
- Nuitka: Ensure `--enable-plugin=tk-inter` flag is present
- PyInstaller: Usually handles this automatically; if it fails, check Python installation includes tcl/tk

### 3. ModuleNotFoundError: No module named 'PIL' / 'openpyxl'

**Symptom**: GIF export or Excel export not available

**Cause**: Conditionally-imported packages missed by packager

**Fix**:
- PyInstaller: Verify `hiddenimports` includes `'PIL'`, `'openpyxl'`
- Nuitka: Verify `--include-module=PIL --include-module=openpyxl` flags

### 4. Antivirus false positive

**Symptom**: Windows Defender or other AV flags the .exe as malware

**Cause**: One-file mode self-extraction mechanism triggers heuristic detection

**Fix**:
- Add the .exe to AV exclusion list
- Sign the executable with a code-signing certificate (eliminates the issue)
- Use one-folder mode (`--onedir` instead of `--onefile`) for lower false positive rate

### 5. Nuitka compilation takes too long

**Symptom**: Nuitka build takes 10-30 minutes

**Cause**: Nuitka compiles Python to C then to machine code; first build is slow

**Fix**:
- Subsequent builds use C compiler cache and are much faster
- Remove `--onefile` to skip compression step

### 6. Large .exe size

**Current**: 80-120 MB is normal, mainly from numpy + matplotlib + tkinter

**Optimization**:
- Install UPX and ensure it's on PATH (PyInstaller uses it automatically)
- Nuitka: add `--lto=yes` for link-time optimization (slower build, smaller binary)
- Add more unused modules to `excludes` in the spec file
