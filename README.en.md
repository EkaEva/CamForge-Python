[中文](README.md) | English

<div align="center">

# CamForge

**Kinematic Simulation System for Pointed Translating Follower Plate Cam Mechanisms**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

---

## Introduction

CamForge is a Python-based desktop application for cam mechanism kinematic simulation, featuring a modern Apple/iOS style UI built with CustomTkinter. It supports six classic follower motion laws, analytical cam profile computation, real-time pressure angle visualization, and full-rotation animation.

### Core Features

- **Six Motion Laws** — Constant velocity, constant acceleration-deceleration, simple harmonic, cycloidal, quintic polynomial, septic polynomial
- **Analytical Computation** — Profile coordinates and pressure angle computed using analytical formulas, high precision
- **Real-time Animation** — Configurable frame count, speed control, pause/resume/replay
- **Roller Follower** — Supports roller radius parameter, automatic actual/theoretical profile computation
- **Modern UI** — CustomTkinter framework, Apple/iOS design style, card-based layout
- **Multilingual UI** — Chinese and English with runtime switching
- **One-click Export** — TIFF (600 DPI), GIF, CSV, Excel, SVG, DXF formats
- **Quick Presets** — 5 built-in presets for one-click loading
- **Keyboard Shortcuts** — Enter to start, Space to pause, Left/Right for frame navigation, R for random

---

## Quick Start

### Requirements

- Python 3.10 or higher
- Windows / macOS / Linux

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python main.py
```

### Download Executable

Visit [GitHub Releases](https://github.com/EkaEva/CamForge/releases) to download the latest Windows executable.

---

## Motion Laws

| No. | Motion Law | Rise Displacement Formula | Characteristics |
|:----:|---------|------------|------|
| 1 | Constant Velocity | $s = h \cdot \dfrac{\delta}{\delta_0}$ | Constant velocity; rigid impact at boundaries |
| 2 | Constant Accel-Decel | $s = 2h\left(\dfrac{\delta}{\delta_0}\right)^2$ (first half) | Constant acceleration; flexible impact at midpoint |
| 3 | Simple Harmonic | $s = \dfrac{h}{2}\left(1 - \cos\dfrac{\pi\delta}{\delta_0}\right)$ | No rigid impact; flexible impact at boundaries |
| 4 | Cycloidal | $s = h\left(\dfrac{\delta}{\delta_0} - \dfrac{1}{2\pi}\sin\dfrac{2\pi\delta}{\delta_0}\right)$ | No rigid or flexible impact |
| 5 | Quintic Polynomial | $s = h\left(10t^3 - 15t^4 + 6t^5\right)$ | High-order smoothness |
| 6 | Septic Polynomial | $s = h\left(35t^4 - 84t^5 + 70t^6 - 20t^7\right)$ | Highest-order smoothness; zero velocity/acceleration at boundaries |

---

## Parameters

| Parameter | Symbol | Description | Constraint |
|-----|:----:|------|------|
| Rise Angle | $\delta_0$ | Cam rotation during rise | Integer, > 1° |
| Outer Dwell Angle | $\delta_{01}$ | Follower at farthest position | Integer, > 1° |
| Return Angle | $\delta_{0}'$ | Cam rotation during return | Integer, > 1° |
| Inner Dwell Angle | $\delta_{02}$ | Follower at nearest position | Integer, > 1° |
| Stroke | $h$ | Maximum follower displacement | > 0 mm |
| Base Circle Radius | $r_0$ | Cam base circle radius | > 0 mm |
| Offset | $e$ | Follower guide offset | < $r_0$ mm |
| Angular Velocity | $\omega$ | Cam rotation speed | > 0 rad/s |
| Roller Radius | $r_r$ | Roller follower radius | < min curvature radius, 0 for knife-edge |

> The four angles must sum to exactly **360°**.

---

## Export Formats

| Type | Format | Description |
|------|------|------|
| Motion Curves | TIFF (600 DPI) | Displacement/velocity/acceleration triple Y-axis curves |
| Geometry Constraints | TIFF (600 DPI) | Pressure angle/curvature radius dual Y-axis curves |
| Profile Plot | TIFF (600 DPI) | Cam profile + base circle + offset circle |
| Animation | GIF (150 DPI) | 360-frame looping animation |
| Data | CSV / Excel | Angle, radius, displacement, velocity, acceleration, curvature, pressure angle |
| Vector | SVG | Motion curves + geometry constraints |
| CAD | DXF | Cam profile, supports AutoCAD import |

---

## Technical Architecture

```
CamForge/
├── main.py                    # GUI entry point
├── cam_mechanics.py           # Kinematics engine
├── i18n.py                    # Internationalization
├── ui/                        # UI module package
│   ├── ctk_constants.py       # CustomTkinter style constants
│   ├── ctk_components.py      # Reusable components
│   ├── ctk_sidebar.py         # Sidebar
│   ├── ctk_toolbar.py         # Toolbar and status bar
│   ├── animation.py           # Animation and GIF generation
│   ├── constants.py           # UI constants
│   ├── drawing.py             # Fixed support drawing
│   ├── export.py              # Export manager
│   ├── i18n_manager.py        # I18n manager
│   ├── params.py              # Parameter model
│   ├── plots.py               # Static chart plotting
│   ├── config.py              # Configuration manager
│   ├── dxf_export.py          # DXF export
│   └── shortcut.py            # Shortcut manager
├── tests/                     # Unit tests
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
└── CamForge.spec              # PyInstaller config
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >= 1.24, < 3 | Numerical computation |
| matplotlib | >= 3.7, < 4 | Chart plotting |
| scipy | >= 1.10, < 2 | Spline interpolation |
| customtkinter | >= 5.2, < 6 | Modern UI framework |
| Pillow | >= 10.0, < 12 | GIF export |
| openpyxl | >= 3.1, < 4 | Excel export |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**CamForge** — Making cam design intuitive and precise

</div>
