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

CamForge is a Python-based desktop application for cam mechanism kinematic simulation, designed for mechanical engineering education and design scenarios. It supports six classic follower motion laws, analytical cam profile computation, real-time pressure angle visualization, and full-rotation animation, helping engineers and students intuitively understand the kinematic characteristics of cam mechanisms.

### Core Highlights

- **Six Motion Laws** — Constant velocity, constant acceleration-deceleration, simple harmonic, cycloidal, fifth-order polynomial, seventh-order polynomial; rise and return can be independently selected
- **Analytical Computation** — Profile coordinates and pressure angle are both computed using analytical formulas (not numerical differentiation), ensuring high precision without jitter
- **Real-time Animation** — Configurable frame count rotation animation with speed control, pause/resume/replay, synchronized pressure angle arcs and normal/tangent lines
- **Roller Follower** — Supports roller radius parameter, automatically computes actual and theoretical profiles with interference warning
- **Modern UI** — CustomTkinter framework, Apple/iOS design style, card-based layout, rounded buttons, toggle switches
- **Multilingual UI** — Supports Chinese and English with runtime switching; export filenames adapt to the selected language
- **One-click Export** — Static charts exported as 600 DPI high-resolution TIFF, animation as 150 DPI looping GIF, data as Excel/CSV, DXF for CAD import
- **Quick Presets** — 5 built-in presets (Default, Small, Large, High Speed, Roller) for one-click loading
- **Batch Export** — Export all formats with one click
- **Parameter Tooltips** — Hover over input fields to see valid ranges
- **Config Persistence** — Automatically saves last-used parameters, export options, UI settings; restored on next launch
- **Keyboard Shortcuts** — Enter to start, Space to pause/resume, Left/Right for frame navigation, R for random cam
- **Random Parameters** — Generate valid random cam parameters with one click for quick exploration
- **Parameter Validation** — Automatic detection of constraints such as sum of four angles, offset range, roller interference

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
cd CamForge
python main.py
```

### Download Executable

Visit [GitHub Releases](https://github.com/EkaEva/CamForge/releases) to download the latest Windows executable (no Python installation required).

---

## Motion Laws Overview

| No. | Motion Law | Rise Displacement Formula | Characteristics |
|:----:|---------|------------|------|
| 1 | Constant Velocity | $s = h \cdot \dfrac{\delta}{\delta_0}$ | Constant velocity; rigid impact at start and end of stroke |
| 2 | Constant Acceleration-Deceleration | $s = 2h\left(\dfrac{\delta}{\delta_0}\right)^2$ (first half) | Constant acceleration; flexible impact at midpoint of stroke |
| 3 | Simple Harmonic | $s = \dfrac{h}{2}\left(1 - \cos\dfrac{\pi\delta}{\delta_0}\right)$ | No rigid impact; flexible impact at start and end of stroke |
| 4 | Cycloidal | $s = h\left(\dfrac{\delta}{\delta_0} - \dfrac{1}{2\pi}\sin\dfrac{2\pi\delta}{\delta_0}\right)$ | No rigid or flexible impact; excellent dynamic performance |
| 5 | Fifth-Order Polynomial | $s = h\left(10t^3 - 15t^4 + 6t^5\right)$ | High-order smoothness; excellent overall performance |
| 6 | Seventh-Order Polynomial | $s = h\left(35t^4 - 84t^5 + 70t^6 - 20t^7\right)$ | Highest-order smoothness; zero velocity and acceleration at boundaries |

---

## Export Formats

| Type | Format | Description |
|------|------|------|
| Motion Curves | TIFF (600 DPI) | Displacement/velocity/acceleration triple Y-axis curves |
| Geometry Constraints | TIFF (600 DPI) | Pressure angle/curvature radius dual Y-axis curves |
| Profile Plot | TIFF (600 DPI) | Cam profile + base circle + offset circle + fixed support |
| Animation | GIF (150 DPI) | 360-frame looping animation with progress indicator |
| CSV | CSV | Angle, radius, displacement, velocity, acceleration, curvature, pressure angle |
| Excel | XLSX | Same as CSV, 7 columns |
| SVG | SVG | Vector graphics: motion curves + geometry constraints |
| DXF | DXF | Cam profile CAD format, supports AutoCAD import |

---

## Technical Architecture

```
CamForge/
├── main.py                    # GUI entry (CustomTkinter + matplotlib)
├── cam_mechanics.py           # Kinematics engine (NumPy vectorized)
├── ui/                        # UI module
│   ├── ctk_constants.py       # CustomTkinter style constants
│   ├── ctk_components.py      # Reusable components
│   ├── ctk_sidebar.py         # Sidebar builder
│   ├── ctk_toolbar.py         # Toolbar and status bar
│   ├── animation.py           # Animation and GIF generation
│   └── ...
├── i18n.py                    # Internationalization (zh/en)
├── tests/                     # Unit tests (143 tests, all pass)
└── ...
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >= 1.24 | Numerical computation |
| matplotlib | >= 3.7 | Chart plotting |
| scipy | >= 1.10 | Spline interpolation |
| customtkinter | >= 5.2, < 6 | Modern UI framework |
| Pillow | >= 10.0 | GIF export |
| openpyxl | >= 3.1 | Excel export |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**CamForge** — Making cam design intuitive and precise

</div>
