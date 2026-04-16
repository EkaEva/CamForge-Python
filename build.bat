@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  CamForge Build Script
echo  Packaging for Windows .exe
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

:: 检查并安装 Nuitka（含 onefile 压缩支持）
python -c "import nuitka" 2>nul || (
    echo [INSTALL] Installing Nuitka with onefile support...
    pip install "nuitka[onefile]"
)
:: 确保 zstandard 已安装（Nuitka onefile 压缩需要）
python -c "import zstandard" 2>nul || (
    echo [INSTALL] Installing zstandard for Nuitka onefile compression...
    pip install zstandard
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
        set HAS_ICON=0
    ) else (
        set HAS_ICON=1
    )
) else (
    set HAS_ICON=1
)

:: --- 清理旧构建产物 ---
echo [CLEAN] Removing previous build artifacts...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "dist_nuitka" rmdir /s /q dist_nuitka

echo.

:: =============================
::  BUILD 1: PyInstaller
:: =============================
echo ============================================
echo  [1/2] Building with PyInstaller...
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

:: =============================
::  BUILD 2: Nuitka
:: =============================
echo ============================================
echo  [2/2] Building with Nuitka...
echo ============================================
echo.

:: 动态解析 matplotlib mpl-data 路径
for /f "delims=" %%i in ('python -c "import matplotlib, os; print(os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data'))"') do set MPL_DATA=%%i

echo [INFO] matplotlib mpl-data: %MPL_DATA%

:: 构建 Nuitka 图标参数
if "%HAS_ICON%"=="1" (
    set NUITKA_ICON=--windows-icon-from-ico=camforge.ico
) else (
    set NUITKA_ICON=
)

python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    %NUITKA_ICON% ^
    --output-filename=CamForge.exe ^
    --output-dir=dist_nuitka ^
    --enable-plugin=tk-inter ^
    --include-module=PIL ^
    --include-module=PIL.Image ^
    --include-module=openpyxl ^
    --include-module=openpyxl.utils ^
    --include-data-dir="%MPL_DATA%=matplotlib/mpl-data" ^
    --include-module=matplotlib.backends.backend_tkagg ^
    --include-module=matplotlib.backends._backend_tk ^
    --nofollow-import-to=tkinter.test ^
    --nofollow-import-to=test ^
    --nofollow-import-to=unittest ^
    --company-name=EkaEva ^
    --product-name=CamForge ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0.0 ^
    --file-description="CamForge - Cam Mechanism Simulator" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Nuitka build FAILED.
    exit /b 1
)

echo.
echo [OK] Nuitka build SUCCESS.

:: 复制 Nuitka 产物到 dist/ 统一目录
if not exist "dist" mkdir dist
if exist "dist_nuitka\CamForge.exe" (
    copy /y "dist_nuitka\CamForge.exe" "dist\CamForge_nuitka.exe" >nul
    for %%A in ("dist\CamForge_nuitka.exe") do echo   Output: dist\CamForge_nuitka.exe  (%%~zA bytes)
) else (
    echo   Output: dist_nuitka\CamForge.exe
)

echo.
echo ============================================
echo  Build complete!
echo  PyInstaller: dist\CamForge.exe
echo  Nuitka:      dist\CamForge_nuitka.exe
echo ============================================

endlocal
