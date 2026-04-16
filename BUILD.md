# CamForge 构建指南

> 将 CamForge 打包为独立 Windows .exe 应用程序

[English](BUILD.en.md) | 中文

---

## 前置条件

- **Python 3.10+**（推荐 3.13）
- **pip 依赖**：`pip install -r requirements.txt`
- **打包工具**：`pip install pyinstaller nuitka`

可选：
- **UPX**：https://upx.github.io/ — 用于压缩可执行文件体积（PyInstaller 自动检测）
- **C 编译器**：Nuitka 编译需要 MSVC（Visual Studio Build Tools）或 MinGW64

---

## 快速构建

```batch
build.bat
```

脚本会自动：
1. 检查并安装 PyInstaller / Nuitka
2. 生成应用图标（如不存在）
3. 清理旧构建产物
4. 执行 PyInstaller 构建 → `dist\CamForge.exe`
5. 执行 Nuitka 构建 → `dist\CamForge_nuitka.exe`

---

## 单独构建

### PyInstaller

```batch
python -m PyInstaller CamForge.spec --noconfirm --clean
```

产物：`dist\CamForge.exe`（单文件，约 80-120 MB）

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

产物：`dist_nuitka\CamForge.exe`（单文件，约 70-100 MB）

---

## 构建产物

| 文件 | 工具 | 大小 | 启动速度 |
|------|------|------|----------|
| `dist\CamForge.exe` | PyInstaller | ~80-120 MB | 首次 ~5-10s（需解压到临时目录） |
| `dist\CamForge_nuitka.exe` | Nuitka | ~70-100 MB | 首次 ~5-10s（需解压到临时目录） |

> 单文件模式首次启动较慢，因为需要将内嵌的依赖解压到临时目录。后续启动会更快（临时文件已缓存）。
> 如需即时启动，可改用单目录模式（去掉 `--onefile`），但会生成一个包含多个文件的文件夹。

---

## 图标

运行 `python make_icon.py` 生成 `camforge.ico`。如需自定义图标，替换此文件即可。

---

## 常见问题

### 1. matplotlib 字体缺失 / 找不到字体

**症状**：运行 .exe 时图表文字显示为方框，或报错 `findfont: Font family ... not found`

**原因**：matplotlib 数据文件（字体、样式表）未被打包

**解决**：
- PyInstaller：确认 `CamForge.spec` 中 `datas=mpl_datas` 和 `collect_data_files('matplotlib')` 生效
- Nuitka：确认 `--include-data-dir=...=matplotlib/mpl-data` 路径正确

### 2. tkinter.TclError: Can't find a usable tk.tcl

**症状**：启动时崩溃，报 Tcl/Tk 相关错误

**原因**：TCL/TK 库未被打包

**解决**：
- Nuitka：确认 `--enable-plugin=tk-inter` 参数
- PyInstaller：通常自动处理；如失败，检查 Python 安装是否包含 tcl/tk

### 3. ModuleNotFoundError: No module named 'PIL' / 'openpyxl'

**症状**：GIF 导出或 Excel 导出功能不可用

**原因**：条件导入的包被打包器遗漏

**解决**：
- PyInstaller：确认 `hiddenimports` 列表包含 `'PIL'`, `'openpyxl'`
- Nuitka：确认 `--include-module=PIL --include-module=openpyxl` 参数

### 4. 杀毒软件误报

**症状**：Windows Defender 或其他杀毒软件将 .exe 标记为恶意软件

**原因**：PyInstaller/Nuitka 单文件模式使用自解压机制，部分杀毒引擎会误判

**解决**：
- 将 .exe 添加到杀毒软件排除列表
- 使用代码签名证书签名可执行文件（可彻底解决）
- 改用单目录模式（`--onedir` 替代 `--onefile`），误报概率更低

### 5. Nuitka 编译时间过长

**症状**：Nuitka 构建耗时 10-30 分钟

**原因**：Nuitka 将 Python 编译为 C 再编译为机器码，首次构建较慢

**解决**：
- 后续构建会利用 C 编译器缓存，速度显著提升
- 可去掉 `--onefile` 加快构建（跳过压缩打包步骤）

### 6. .exe 体积过大

**现状**：80-120 MB 是正常范围，主要由 numpy + matplotlib + tkinter 贡献

**优化**：
- 安装 UPX 并确保在 PATH 中（PyInstaller 自动使用）
- Nuitka 添加 `--lto=yes` 启用链接时优化（构建更慢，体积更小）
- 在 spec 文件 `excludes` 中添加更多不需要的模块
