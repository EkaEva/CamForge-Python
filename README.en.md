[中文](README.md) | English | [日本語](README.ja.md)

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
- **Real-time Animation** — 360-frame rotation animation with speed control, pause/resume, synchronized pressure angle arcs and normal/tangent lines
- **One-click Export** — Static charts exported as high-resolution PNG, animation exported as looping GIF
- **Random Parameters** — Generate valid random cam parameters with one click for quick exploration of different configurations
- **Parameter Validation** — Automatic detection of constraints such as sum of four angles and offset range, with instant alerts for invalid parameters

---

## Feature Showcase

### Interface Layout

```
┌──────────────────────────────────────────────────────────────┐
│  CamForge - Cam Simulation                                   │
├────────────┬─────────────────────────────────────────────────┤
│            │  ┌─────────────┐  ┌─────────────┐              │
│  Parameter │  │ Displacement│  │  Velocity   │              │
│   Panel    │  │   curve s   │  │  curve v    │              │
│  ────────  │  └─────────────┘  └─────────────┘              │
│  Rise angle│  ┌─────────────┐  ┌─────────────┐              │
│  Far dwell │  │ Acceleration│  │ Cam profile │              │
│  Return ang│  │  curve a    │  │             │              │
│  Near dwell│  └─────────────┘  └─────────────┘              │
│  Stroke/   │  ┌───────────────────────────────┐              │
│  Base circ │  │                               │              │
│  Offset/ω  │  │  Cam rotation animation +     │              │
│  Motion law│  │       Info panel              │              │
│  Rotation  │  │                               │              │
│  Offset dir│  └───────────────────────────────┘              │
│            │                                                 │
├────────────┴─────────────────────────────────────────────────┤
│  [▶ Start]  [⏸ Pause]  [Clear Params]  [Clear Charts]       │
│  [Random Cam]  [Download]  Speed: ━━━━━●━━━━━               │
│  ☑Displacement ☑Velocity ☑Acceleration ☑Animation            │
└──────────────────────────────────────────────────────────────┘
```

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
- **Pressure Angle Arc**: Real-time drawing of pressure angle arc and annotation at the contact point
- **Normal/Tangent Lines**: Analytically computed profile derivative directions for precise normal and tangent line drawing at the contact point
- **Phase Boundary Lines**: Radial markings for the four phases — rise, far dwell, return, near dwell
- **Info Panel**: Real-time display of current rotation angle, pressure angle, displacement, stroke, and initial displacement

---

## Quick Start

### Requirements

- Python 3.10 or above
- Windows / macOS / Linux

### Install Dependencies

```bash
pip install numpy>=1.20 matplotlib>=3.5 Pillow
```

> **Note**: `Pillow` is used for GIF animation export and is not included in `requirements.txt`; it must be installed manually.

### Launch Application

```bash
cd CamForge
python main.py
```

---

## User Guide

### 1. Parameter Input

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

### 2. Select Motion Law

- **Rise law**: Dropdown to select motion law 1-5
- **Return law**: Dropdown to select motion law 1-5
- **Rotation direction**: Clockwise / Counterclockwise
- **Offset direction**: Positive offset / Negative offset

### 3. Run Simulation

1. Click the **"Start"** button to compute and plot static curves and cam profile
2. Animation starts automatically, showing the cam rotation process
3. Use the **"Pause"** button to pause/resume the animation
4. Drag the **speed slider** to adjust animation frame rate (1 = slowest, 10 = fastest)

### 4. Export Results

- Check the chart types to export (displacement / velocity / acceleration / animation)
- Click the **"Download"** button
- Static charts are saved as **PNG** (150 DPI), animation is saved as **GIF** (looping)

### 5. Random Exploration

Click the **"Random Cam"** button to automatically generate a set of valid random parameters for quick exploration of different cam configurations.

---

## Technical Architecture

```
CamForge/
├── main.py              # GUI application entry (tkinter + matplotlib)
│   ├── CamSimulator     # Main window class
│   │   ├── _build_gui()       # Build interface layout
│   │   ├── _on_start()        # Start simulation computation
│   │   ├── _animate()         # Animation loop
│   │   ├── _on_download()     # Export images/GIF
│   │   └── ...                # Event handling and drawing
│   └── generate_random_params()  # Random parameter generator
│
├── cam_mechanics.py     # Kinematic computation engine (pure math, no GUI dependency)
│   ├── compute_rise()          # Rise motion law computation
│   ├── compute_return()        # Return motion law computation
│   ├── compute_full_motion()   # Full-stroke motion synthesis
│   ├── compute_cam_profile()   # Cam profile coordinate computation
│   ├── compute_pressure_angle()# Pressure angle analytical computation
│   ├── compute_rotated_cam()   # Cam rotation (animation frame)
│   ├── compute_anim_frame_data()# Animation frame data analytical computation
│   ├── compute_pressure_angle_arc()# Pressure angle arc coordinates
│   └── validate_params()       # Parameter validity check
│
└── requirements.txt     # Python dependency declaration
```

### Design Principles

- **Separation of Computation and Presentation**: `cam_mechanics.py` is a pure math library with no GUI framework dependencies; it can be used independently for batch computation or integration into other projects
- **Analytical First**: All derivatives and pressure angles use analytical formulas (`ds/dδ = v/ω`), avoiding precision loss from numerical differentiation
- **1° Step Discretization**: 360 discrete points across the full stroke, with one computation point per integer degree, balancing precision and performance

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
| [Pillow](https://python-pillow.org/) | Any | GIF animation export |
| tkinter | Standard library | GUI framework (bundled with Python) |

---

## FAQ

<details>
<summary><b>Chinese characters display as squares after launch</b></summary>

This application uses SimHei / Microsoft YaHei fonts to render Chinese text. If your system lacks these fonts:
- **Windows**: Generally bundled with the OS, no action needed
- **macOS**: Install the SimHei font or modify `plt.rcParams['font.sans-serif']` in `main.py` to a Chinese font available on your system
- **Linux**: Run `sudo apt install fonts-wqy-microhei` and update the font configuration

</details>

<details>
<summary><b>Animation playback stutters</b></summary>

- Lower the speed slider setting
- Disable unnecessary display options (normal/tangent lines, grid, etc.)
- Animation refreshes the canvas every 2 frames by default to reduce latency

</details>

<details>
<summary><b>GIF export fails</b></summary>

Make sure Pillow is installed: `pip install Pillow`. GIF export requires rendering 360 frames sequentially, which takes a long time — please wait patiently for the progress indicator.

</details>

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**CamForge** — Making cam design intuitive and precise

</div>
