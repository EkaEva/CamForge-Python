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

CamForge is a Python-based desktop application for cam mechanism kinematic simulation, designed for mechanical engineering education and design scenarios. It supports five classic follower motion laws, analytical cam profile computation, real-time pressure angle visualization, and full-rotation animation, helping engineers and students intuitively understand the kinematic characteristics of cam mechanisms.

### Core Highlights

- **Five Motion Laws** — Constant velocity, constant acceleration-deceleration, simple harmonic, cycloidal, and fifth-order polynomial; rise and return can be independently selected
- **Analytical Computation** — Profile coordinates and pressure angle are both computed using analytical formulas (not numerical differentiation), ensuring high precision without jitter
- **Real-time Animation** — 360-frame rotation animation with speed control, pause/resume/replay, synchronized pressure angle arcs and normal/tangent lines
- **Multilingual UI** — Supports Chinese and English with runtime switching; export filenames adapt to the selected language
- **One-click Export** — Static charts exported as 600 DPI high-resolution TIFF, animation as 150 DPI looping GIF, data as Excel spreadsheet
- **Random Parameters** — Generate valid random cam parameters with one click for quick exploration of different configurations
- **Parameter Validation** — Automatic detection of constraints such as sum of four angles and offset range, with instant alerts for invalid parameters
- **Keyboard Shortcuts** — Enter to start, Space to pause/resume/replay, R for random cam

---

## Feature Showcase

### Interface Layout

**v0.4.1 New Layout**:

```
┌────────────┬──────────────────────────────────────────────────────────────┐
│            │  [Start] [Pause] [Clear] [Random] [Load] [Save] [Download]   │
│  Language  ├───────────────────┬────────┬────────────────────┬───────────┤
│  ────────  │  ┌─────────────┐  │        │                    │           │
│  Motion    │  │ Follower    │  │        │                    │  Info     │
│  Params    │  │ Motion Curves│  │ Spacer │    Cam Animation   │  Panel    │
│  Rise angle│  └─────────────┘  │        │   (Profile+Follower)│  (Real-   │
│  Far dwell ├───────────────────┤        │                    │  time)    │
│  Return ang│  ┌─────────────┐  │        │                    │           │
│  Near dwell│  │ Geometry    │  │        │                    │           │
│  Stroke/   │  │ Constraints │  │        │                    │           │
│  Base circ │  └─────────────┘  │        │                    │           │
│  Offset/ω  │                   │        │                    │           │
│  Motion law│  Left: Static     │ Spacer │  Right: Dynamic     │           │
│  Rotation  │                   │        │                    │           │
│  Offset dir│                   │        │                    │           │
│  ────────  │                   │        │                    │           │
│  Display   │                   │        │                    │           │
│  ☐Tangent  │                   │        │                    │           │
│  ☐Normal   │                   │        │                    │           │
│  ☐Press.arc│                   │        │                    │           │
│  ☐Boundaries│                  │        │                    │           │
│  ☐Base circ│                   │        │                    │           │
│  ☐Offset ○ │                   │        │                    │           │
│  ☐Limits   │                   │        │                    │           │
│  ☐Grid     │                   │        │                    │           │
└────────────┴───────────────────┴────────┴────────────────────┴───────────┘
```

**Layout Features**:
- **Three-column layout**: Static charts | Spacer | Dynamic animation
- **Left side**: Follower motion curves (top, Triple Y-axis) | Geometry constraints (bottom, Dual Y-axis)
- **Right side**: Cam animation (main area) | Info panel (embedded in top-left corner)
- **Spacer column**: Provides enough room for right Y-axes in motion curves
- **Two-row status bar**: Row 1 shows status message, Row 2 shows stroke, initial displacement, max pressure angle
- **Adaptive Scaling**: Automatically adjusts chart sizes when window changes, no clipping or white space

### Motion Laws Overview

| No. | Motion Law | Rise Displacement Formula | Characteristics |
|:----:|---------|------------|------|
| 1 | Constant Velocity | $s = h \cdot \dfrac{\delta}{\delta_0}$ | Constant velocity; rigid impact at start and end of stroke |
| 2 | Constant Acceleration-Deceleration | $s = 2h\left(\dfrac{\delta}{\delta_0}\right)^2$ (first half) | Constant acceleration; flexible impact at midpoint of stroke |
| 3 | Simple Harmonic | $s = \dfrac{h}{2}\left(1 - \cos\dfrac{\pi\delta}{\delta_0}\right)$ | No rigid impact; flexible impact at start and end of stroke |
| 4 | Cycloidal | $s = h\left(\dfrac{\delta}{\delta_0} - \dfrac{1}{2\pi}\sin\dfrac{2\pi\delta}{\delta_0}\right)$ | No rigid or flexible impact; excellent dynamic performance |
| 5 | Fifth-Order Polynomial | $s = h\left(10t^3 - 15t^4 + 6t^5\right)$ | High-order smoothness; best overall performance |

### Animation Features

- **Inversion Method**: Cam rotates while follower remains fixed, intuitively demonstrating actual motion
- **Fixed Support**: Standard pinned support symbol (pin circle + triangle + hatched base) drawn at the rotation center
- **Pressure Angle Arc**: Real-time drawing of pressure angle arc and annotation at the contact point
- **Normal/Tangent Lines**: Analytically computed profile derivative directions for precise normal and tangent line drawing at the contact point
- **Phase Boundary Lines**: Radial markings for the four phases — rise, far dwell, return, near dwell
- **Info Panel**: Real-time display of current rotation angle, pressure angle, displacement, stroke, and initial displacement
- **Configurable Display**: 8 display options (tangent, normal, pressure angle arc, phase boundaries, base circle, offset circle, follower limits, grid); exported GIF matches the on-screen display exactly

---

## Quick Start

### Requirements

- Python 3.10 or above
- Windows / macOS / Linux

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Launch Application

```bash
cd CamForge
python main.py
```

---

## User Guide

### 1. Language Switching

Select a language (Chinese / English) at the top of the sidebar. All labels, buttons, plot titles, status messages, and export filenames switch instantly.

### 2. Parameter Input

Enter cam design parameters in the left panel:

| Parameter | Symbol | Description | Constraint |
|-----|:----:|------|------|
| Rise motion angle | $\delta_0$ | Cam rotation angle during rise phase | Integer, > 1° |
| Far dwell angle | $\delta_{01}$ | Follower stays at farthest position | Integer, > 1° |
| Return motion angle | $\delta_{0}'$ | Cam rotation angle during return phase | Integer, > 1° |
| Near dwell angle | $\delta_{02}$ | Follower stays at nearest position | Integer, > 1° |
| Stroke | $h$ | Maximum follower displacement | > 0 mm |
| Base circle radius | $r_0$ | Cam base circle radius | > 0 mm |
| Offset | $e$ | Follower guide offset | < $r_0$ mm |
| Angular velocity | $\omega$ | Cam rotation angular velocity | > 0 rad/s |

> The sum of the four angles must equal exactly **360°**.

### 3. Select Motion Law

- **Rise law**: Dropdown to select motion law 1-5
- **Return law**: Dropdown to select motion law 1-5
- **Rotation direction**: Clockwise / Counterclockwise
- **Offset direction**: Positive offset / Negative offset

### 4. Run Simulation

1. Click the **"Start"** button (or press Enter) to compute and plot static curves and cam profile
2. Animation starts automatically, showing the cam rotation process
3. Use the **"Pause"** button to pause/resume the animation (or press Space)
4. After animation ends, press Space or click **"Replay"** to restart
5. Drag the **speed slider** to adjust animation frame rate (1 = slowest, 10 = fastest)

### 5. Display Options

The "Display Options" section in the sidebar provides 8 checkboxes controlling auxiliary elements in the animation view:

| Option | Description | Default |
|--------|-------------|:-------:|
| Tangent | Tangent line at contact point | Off |
| Normal | Normal line at contact point | Off |
| Pressure Angle Arc | Pressure angle arc and reference line | Off |
| Phase Boundaries | Radial phase boundary lines | Off |
| Base Circle | Base circle outline | Off |
| Offset Circle | Offset circle outline | Off |
| Follower Limits | Upper/lower limit horizontal lines | Off |
| Grid | Coordinate grid | Off |

> When exporting GIF, display options match the on-screen view — only checked elements appear in the export.

### 6. Export Results

Check the items to export, then click the **"Download"** button:

| Type | Format | Description |
|------|--------|-------------|
| Displacement | TIFF (600 DPI) | Follower displacement vs. angle |
| Velocity | TIFF (600 DPI) | Follower velocity vs. angle |
| Acceleration | TIFF (600 DPI) | Follower acceleration vs. angle |
| Cam Profile | TIFF (600 DPI) | Cam profile + base circle + offset circle + fixed support |
| Animation | GIF (150 DPI) | 360-frame looping animation with progress indicator |
| Excel | XLSX | Angle δ, Radius R, Velocity v, Acceleration a |

### 7. Random Exploration

Click the **"Random Cam"** button (or press R) to automatically generate a set of valid random parameters for quick exploration of different cam configurations.

---

## Technical Architecture

```
CamForge/
├── main.py                    # GUI application entry (tkinter + matplotlib)
│   ├── CamSimulator           # Main window class (composition pattern)
│   │   ├── I18nManager        # Internationalization manager (delegation)
│   │   ├── ThemeManager       # Theme manager (delegation)
│   │   ├── SidebarBuilder     # Sidebar builder (delegation)
│   │   ├── ExportManager      # Export manager (delegation)
│   │   └── AnimationController# Animation controller (delegation)
│
├── cam_mechanics.py           # Kinematic computation engine (pure math, NumPy vectorized)
│   ├── compute_full_motion()  # Full-stroke motion synthesis
│   ├── compute_cam_profile()  # Cam profile coordinate computation
│   ├── compute_roller_profile()# Roller actual profile (vectorized)
│   ├── compute_curvature_radius()# Curvature radius (vectorized)
│   ├── compute_pressure_angle()# Pressure angle analytical computation
│   ├── compute_rotated_cam()  # Cam rotation (animation frame)
│   ├── compute_anim_frame_data()# Animation frame data analytical computation
│   ├── compute_pressure_angle_arc()# Pressure angle arc coordinates
│   └── validate_params()      # Parameter validity check
│
├── ui/                        # UI module package
│   ├── __init__.py
│   ├── animation.py           # Animation rendering and GIF generation
│   ├── constants.py           # UI constants and theme colors
│   ├── drawing.py             # Fixed support drawing
│   ├── export.py              # Export manager (TIFF/SVG/CSV/Excel/GIF)
│   ├── i18n_manager.py        # Internationalization manager
│   ├── params.py              # ParameterModel parameter model
│   ├── plots.py               # Static chart plotting functions
│   ├── sidebar.py             # Sidebar builder
│   └── theme.py               # Theme manager (control caching)
│
├── i18n.py                    # Internationalization module (zh/en bilingual)
│   ├── TRANSLATIONS           # Translation dictionary
│   ├── FONT_MAP               # Cross-platform font mapping
│   └── t()                    # Translation lookup function
│
├── tests/                     # Unit tests (pytest, 136 tests all passing)
│   ├── test_cam_mechanics.py  # Kinematic computation tests
│   ├── test_i18n.py           # Internationalization tests
│   └── test_ui.py             # UI module tests
│
├── requirements.txt           # Python dependency declaration
├── LICENSE                    # MIT open source license
└── .gitignore                 # Git ignore rules
```

### Design Principles (v0.2)

- **Composition Pattern**: CamSimulator uses composition to delegate managers, clear responsibilities, easy to maintain
- **Computation and Presentation Separation**: `cam_mechanics.py` is a pure math library, no GUI framework dependency
- **NumPy Vectorization**: `compute_roller_profile` and `compute_curvature_radius` use `np.roll` instead of Python loops, 10x+ performance improvement
- **Analytical First**: All derivatives and pressure angles use analytical formulas (`ds/dδ = v/ω`), avoiding precision loss from numerical differentiation
- **1° Step Discretization**: 360 discrete points across the full stroke, one computation point per integer degree, balancing precision and performance
- **Internationalization Design**: All UI strings resolved via i18n key lookup, runtime language switch without restart
- **Control Caching**: Theme switching traverses cached control list instead of recursively traversing control tree, 5x+ performance improvement
- **ParameterModel**: Type-safe parameter model, replaces naked dict passing, supports validation and conversion

---

## Core Algorithms

### Cam Profile Computation (Inversion Method)

Profile coordinates are analytically derived using the inversion method:

$$
x = -s_n \left[ (s_0 + s)\sin\delta + p_z \cdot e\cos\delta \right]
$$

$$
y = (s_0 + s)\cos\delta - p_z \cdot e\sin\delta
$$

where $s_0 = \sqrt{r_0^2 - e^2}$, $s_n = \pm 1$ is the rotation direction sign, and $p_z = \pm 1$ is the offset sign.

### Pressure Angle Computation

$$
\alpha = \arctan\!\left(\frac{ds/d\delta - p_z \cdot e}{s_0 + s}\right)
$$

When the maximum pressure angle exceeds **30°**, a red warning will be displayed on the interface.

---

## Dependencies

| Dependency | Version Requirement | Purpose |
|-----|---------|------|
| [numpy](https://numpy.org/) | >= 1.20 | Numerical computation (array operations, trigonometric functions) |
| [matplotlib](https://matplotlib.org/) | >= 3.5 | Chart plotting and tkinter embedding |
| [Pillow](https://python-pillow.org/) | >= 9.0 | GIF animation export |
| [openpyxl](https://openpyxl.readthedocs.io/) | >= 3.0 | Excel data export |
| tkinter | Standard library | GUI framework (bundled with Python) |

---

## FAQ

<details>
<summary><b>Chinese characters display as squares after launch</b></summary>

This application automatically detects available system fonts and falls back as needed. If issues persist:
- **Windows**: Generally bundled with the OS, no action needed
- **macOS**: The app auto-detects Yu Gothic / Hiragino Sans etc.
- **Linux**: Run `sudo apt install fonts-wqy-microhei` and update the font configuration

</details>

<details>
<summary><b>Animation playback stutters</b></summary>

- Lower the speed slider setting
- Disable unnecessary display options (normal/tangent lines, grid, etc.)
- Animation refreshes the canvas every 2 frames by default to reduce latency

</details>

<details>
<summary><b>GIF export takes a long time</b></summary>

GIF export renders 360 frames sequentially using a background thread with a progress bar to avoid UI freezing. After frame rendering, GIF composition is performed — the progress label will show "Composing GIF...". Please wait patiently.

</details>

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**CamForge** — Making cam design intuitive and precise

</div>
