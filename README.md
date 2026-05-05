中文 | [English](README.en.md)

> ⚠️ **项目已迁移 / Project Moved**
>
> 本项目已停止维护，后续开发已迁移至新仓库：
>
> **新仓库地址：[https://github.com/EkaEva/CamForge-Next](https://github.com/EkaEva/CamForge)**
>
> 新版本 **CamForge** 采用全新技术栈重构：
> - **Tauri v2 + SolidJS + Rust** 实现跨平台桌面应用
> - 支持 **Web 服务器** 和 **Docker** 部署模式
> - 前后端分离架构，Rust 高性能计算引擎
> - 移动端响应式布局与触摸手势支持
> - 撤销/重做、无障碍性改进、GIF 异步导出
>
> 欢迎前往新仓库查看最新版本。
>
> ---

<div align="center">

# CamForge

**尖顶直动从动件盘形凸轮机构运动学仿真系统**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

---

## 简介

CamForge 是一款基于 Python 的凸轮机构运动学仿真桌面应用，采用 CustomTkinter 框架实现现代化 Apple/iOS 风格界面。支持六种经典从动件运动规律、凸轮廓形解析计算、压力角实时可视化以及全程旋转动画，帮助工程师和学生直观理解凸轮机构的运动学特性。

### 核心功能

- **六种运动规律** — 等速、等加速等减速、简谐、摆线、五次多项式、七次多项式
- **解析计算** — 廓形坐标与压力角均采用解析公式，精度高、无跳动
- **实时动画** — 可配置帧数旋转动画，支持速度调节、暂停/继续/重播
- **滚子从动件** — 支持滚子半径参数，自动计算实际廓形与理论廓形
- **现代化 UI** — CustomTkinter 框架，Apple/iOS 设计风格，卡片式布局
- **多语言界面** — 支持中文、英文双语实时切换
- **一键导出** — TIFF (600 DPI)、GIF、CSV、Excel、SVG、DXF 格式
- **快速预设** — 内置 5 种常用凸轮预设
- **键盘快捷键** — Enter 开始、Space 暂停、Left/Right 跳帧、R 随机

---

## 快速开始

### 环境要求

- Python 3.10 及以上
- Windows / macOS / Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
python main.py
```

### 下载可执行文件

前往 [GitHub Releases](https://github.com/EkaEva/CamForge/releases) 下载最新版本的 Windows 可执行文件。

---

## 运动规律

| 编号 | 运动规律 | 推程位移公式 | 特性 |
|:----:|---------|------------|------|
| 1 | 等速运动 | $s = h \cdot \dfrac{\delta}{\delta_0}$ | 速度恒定，行程始末有刚性冲击 |
| 2 | 等加速等减速 | $s = 2h\left(\dfrac{\delta}{\delta_0}\right)^2$（前半段） | 加速度恒定，行程中点有柔性冲击 |
| 3 | 简谐运动 | $s = \dfrac{h}{2}\left(1 - \cos\dfrac{\pi\delta}{\delta_0}\right)$ | 无刚性冲击，行程始末有柔性冲击 |
| 4 | 摆线运动 | $s = h\left(\dfrac{\delta}{\delta_0} - \dfrac{1}{2\pi}\sin\dfrac{2\pi\delta}{\delta_0}\right)$ | 无刚性冲击和柔性冲击 |
| 5 | 五次多项式 | $s = h\left(10t^3 - 15t^4 + 6t^5\right)$ | 高阶平滑，综合性能优 |
| 6 | 七次多项式 | $s = h\left(35t^4 - 84t^5 + 70t^6 - 20t^7\right)$ | 最高阶平滑，边界速度加速度均为零 |

---

## 参数说明

| 参数 | 符号 | 说明 | 约束 |
|-----|:----:|------|------|
| 推程运动角 | $\delta_0$ | 推程阶段凸轮转角 | 整数，> 1° |
| 远休止角 | $\delta_{01}$ | 从动件停留在最远位置 | 整数，> 1° |
| 回程运动角 | $\delta_{0}'$ | 回程阶段凸轮转角 | 整数，> 1° |
| 近休止角 | $\delta_{02}$ | 从动件停留在最近位置 | 整数，> 1° |
| 行程 | $h$ | 从动件最大位移 | > 0 mm |
| 基圆半径 | $r_0$ | 凸轮基圆半径 | > 0 mm |
| 偏距 | $e$ | 从动件导路偏移量 | < $r_0$ mm |
| 角速度 | $\omega$ | 凸轮旋转角速度 | > 0 rad/s |
| 滚子半径 | $r_r$ | 滚子从动件半径 | < 最小曲率半径，0 为尖顶 |

> 四个角度之和必须恰好等于 **360°**。

---

## 导出格式

| 类型 | 格式 | 说明 |
|------|------|------|
| 运动线图 | TIFF (600 DPI) | 推杆位移/速度/加速度三 Y 轴曲线 |
| 几何约束 | TIFF (600 DPI) | 压力角/曲率半径双 Y 轴曲线 |
| 廓形图 | TIFF (600 DPI) | 凸轮廓形 + 基圆 + 偏距圆 |
| 动画 | GIF (150 DPI) | 360 帧循环动画 |
| 数据 | CSV / Excel | 转角、向径、位移、速度、加速度、曲率半径、压力角 |
| 矢量图 | SVG | 运动线图 + 几何约束 |
| CAD | DXF | 凸轮廓形，支持 AutoCAD 导入 |

---

## 技术架构

```
CamForge/
├── main.py                    # GUI 应用入口
├── cam_mechanics.py           # 运动学计算引擎
├── i18n.py                    # 国际化模块
├── ui/                        # UI 模块包
│   ├── ctk_constants.py       # CustomTkinter 样式常量
│   ├── ctk_components.py      # 可复用组件
│   ├── ctk_sidebar.py         # 侧边栏
│   ├── ctk_toolbar.py         # 工具栏和状态栏
│   ├── animation.py           # 动画渲染与 GIF 生成
│   ├── constants.py           # UI 常量
│   ├── drawing.py             # 固定铰支座绘制
│   ├── export.py              # 导出管理器
│   ├── i18n_manager.py        # 国际化管理器
│   ├── params.py              # 参数模型
│   ├── plots.py               # 静态图表绘制
│   ├── config.py              # 配置管理器
│   ├── dxf_export.py          # DXF 导出
│   └── shortcut.py            # 快捷键管理器
├── tests/                     # 单元测试
├── requirements.txt           # Python 依赖
├── pyproject.toml             # 项目配置
└── CamForge.spec              # PyInstaller 打包配置
```

---

## 依赖

| 依赖 | 版本要求 | 用途 |
|-----|---------|------|
| numpy | >= 1.24, < 3 | 数值计算 |
| matplotlib | >= 3.7, < 4 | 图表绘制 |
| scipy | >= 1.10, < 2 | 样条插值 |
| customtkinter | >= 5.2, < 6 | 现代化 UI 框架 |
| Pillow | >= 10.0, < 12 | GIF 动画导出 |
| openpyxl | >= 3.1, < 4 | Excel 数据导出 |

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

<div align="center">

**CamForge** — 让凸轮设计直观而精确

</div>
