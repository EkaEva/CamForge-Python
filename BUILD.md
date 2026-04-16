# CamForge 构建指南

> 将 CamForge 打包为独立 Windows .exe 应用程序

[English](BUILD.en.md) | 中文

---

## 前置条件

- **Python 3.10+**（推荐 3.13）
- **pip 依赖**：`pip install -r requirements.txt`
- **PyInstaller**：`pip install pyinstaller`

可选：
- **UPX**：https://upx.github.io/ — 用于压缩可执行文件体积（PyInstaller 自动检测）

---

## 快速构建

```batch
build.bat
```

脚本会自动：
1. 检查并安装 PyInstaller
2. 生成应用图标（如不存在）
3. 清理旧构建产物
4. 执行 PyInstaller 构建 → `dist\CamForge.exe`

---

## 手动构建

```batch
python -m PyInstaller CamForge.spec --noconfirm --clean
```

产物：`dist\CamForge.exe`（单文件，约 70 MB）

---

## 图标

运行 `python make_icon.py` 生成 `camforge.ico`。如需自定义图标，替换此文件即可。

---

## 常见问题

### 1. matplotlib 字体缺失 / 找不到字体

**症状**：运行 .exe 时图表文字显示为方框，或报错 `findfont: Font family ... not found`

**原因**：matplotlib 数据文件（字体、样式表）未被打包

**解决**：确认 `CamForge.spec` 中 `datas=mpl_datas` 和 `collect_data_files('matplotlib')` 生效

### 2. tkinter.TclError: Can't find a usable tk.tcl

**症状**：启动时崩溃，报 Tcl/Tk 相关错误

**原因**：TCL/TK 库未被打包

**解决**：检查 Python 安装是否包含 tcl/tk 组件

### 3. ModuleNotFoundError: No module named 'PIL' / 'openpyxl'

**症状**：GIF 导出或 Excel 导出功能不可用

**原因**：条件导入的包被打包器遗漏

**解决**：确认 `hiddenimports` 列表包含 `'PIL'`, `'openpyxl'`

### 4. 杀毒软件 / 防火墙提示"未知发布者"

**症状**：Windows Defender 或防火墙提示"未知发布者"或标记为风险软件

**原因**：未签名的可执行文件会触发 Windows SmartScreen 警告

**解决**：
- 点击"更多信息" → "仍要运行"即可正常使用
- 如需彻底消除警告，需使用代码签名证书（EV 代码签名证书可立即获得 SmartScreen 信任）
- 将 .exe 添加到杀毒软件排除列表

### 5. 首次启动较慢

**症状**：双击 .exe 后需要 5-10 秒才出现窗口

**原因**：单文件模式首次启动需要将内嵌的依赖解压到临时目录

**解决**：后续启动会更快（临时文件已缓存）
