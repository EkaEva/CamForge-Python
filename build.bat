@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  CamForge Build Script
echo  Packaging for Windows .exe (PyInstaller)
echo ============================================
echo.

:: --- 前置条件检查 ---
where python >nul 2>&1 || (
    echo [ERROR] Python not found on PATH
    exit /b 1
)

echo [CHECK] Python found:
python --version

:: 检查并安装 PyInstaller
python -c "import PyInstaller" 2>nul || (
    echo [INSTALL] Installing PyInstaller...
    pip install pyinstaller
)

:: 验证项目依赖
python -c "import numpy, matplotlib, PIL, openpyxl" 2>nul || (
    echo [ERROR] Missing project dependencies. Run: pip install -r requirements.txt
    exit /b 1
)
echo [OK] All project dependencies satisfied.

:: --- 图标文件 ---
if not exist "camforge.ico" (
    echo [INFO] camforge.ico not found. Generating icon...
    python make_icon.py
    if not exist "camforge.ico" (
        echo [WARN] Icon generation failed. Building without icon.
    )
)

:: --- 清理旧构建产物 ---
echo [CLEAN] Removing previous build artifacts...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.

:: =============================
::  Build: PyInstaller
:: =============================
echo ============================================
echo  Building with PyInstaller...
echo ============================================
echo.

python -m PyInstaller CamForge.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build FAILED.
    exit /b 1
)

echo.
echo [OK] PyInstaller build SUCCESS.
if exist "dist\CamForge.exe" (
    for %%A in ("dist\CamForge.exe") do echo   Output: dist\CamForge.exe  (%%~zA bytes)
) else (
    echo   Output: dist\CamForge.exe
)

echo.
echo ============================================
echo  Build complete!
echo  Output: dist\CamForge.exe
echo ============================================

endlocal
