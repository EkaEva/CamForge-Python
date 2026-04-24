[中文](ROADMAP.md) | English

# CamForge Roadmap

> ⚠️ **Project Moved**
>
> This project is no longer maintained. Development has moved to a new repository:
>
> **New Repository: [https://github.com/EkaEva/CamForge-Next](https://github.com/EkaEva/CamForge-Next)**
>
> The new version includes architecture restructuring, flat-faced follower support, inverse design features, and more.
> The v0.7.0 development plan in this ROADMAP will be continued in the new project.
>
> ---

> Current status analysis and future optimization directions

---

## I. Existing Issues

### 1.1 Code Architecture

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 1 | `CamSimulator` class exceeds **1350 lines**; GUI construction, computation, animation, export, and i18n logic are all coupled | `main.py` | High |
| 2 | `_build_gui` method is ~**270 lines**; sidebar/toolbar/chart layout all inline, label+entry pattern repeated 8 times without extraction | `main.py:261-565` | Medium |
| 3 | Computation state (`sim_data`) and GUI state (widget references, animation flags) are stored in the same class with no independent data model | `main.py:149-180` | Medium |

### 1.2 Robustness

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 4 | GIF export thread reads `sim_data` without lock protection; `saved_list.append()` and main thread are concurrent without synchronization | `main.py:1273-1438` | High |
| 5 | `_on_start` has no try/except wrapping `compute_full_motion`/`compute_cam_profile`; application crashes on exception | `main.py:672-735` | Medium |
| 6 | `_read_params` silently truncates floating-point angles (`int(float(...))`); user input 90.9 becomes 90 with no notification | `main.py:629-639` | Medium |
| 7 | `validate_params` allows `e < 0` (checks `abs(e)`), but `compute_cam_profile` rejects `e < 0`; inconsistent | `cam_mechanics.py:541 vs 289` | Medium |
| 8 | `_export_excel` `wb.save()` has no try/except; crashes on disk full or invalid path | `main.py` | Medium |
| 9 | `fig.savefig()` calls in `_on_download` have no error handling | `main.py` | Medium |
| 10 | `_on_close` does not wait for GIF export thread to finish; may interrupt export | `main.py` | Low |

### 1.3 Computation Engine

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 11 | `compute_full_motion` calculates `i1/i2/i3` via `int(round(...))`; when four angles sum to 360, i3 may not equal 360, causing index out of bounds | `cam_mechanics.py:226-228` | High |
| 12 | `compute_full_motion` does not verify four angles sum to 360°; only `validate_params` checks, direct calls can produce incorrect results | `cam_mechanics.py:168-262` | Medium |
| 13 | `compute_anim_frame_data` does not validate frame index `i` range (`0 <= i < len(s)`); IndexError with no description on out of bounds | `cam_mechanics.py:369-450` | Medium |
| 14 | When `e ≈ r_0`, `s_0` is very small, `s_0 + s` in `compute_pressure_angle` approaches zero, pressure angle jumps to ±90° with no warning | `cam_mechanics.py:296,336` | Medium |
| 15 | `compute_rise` allows `h=0` but `compute_full_motion` rejects `h<=0`; API inconsistency | `cam_mechanics.py:35 vs 198` | Low |
| 16 | `N_POINTS = 360` hardcoded; resolution not adjustable | `cam_mechanics.py:8` | Low |

### 1.4 Internationalization

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 17 | `compute_rise`/`compute_return` `ValueError` messages are pure English, not going through i18n; Chinese users see English when exceptions propagate to UI | `cam_mechanics.py:33-39,108-115` | Medium |
| 18 | `error.unknown_law` in `cam_mechanics.py` uses pipe format `error.unknown_law|{law}`, which does not match i18n key `error.unknown_law`; translation never matches | `cam_mechanics.py:83,159` | Medium |
| 19 | Motion law combobox Chinese "规律" suffix inconsistent (laws 1/2 omit, laws 3/4/5 include) | `i18n.py:law.combo.*` | Low |
| 20 | Logo text "CamForge", GIF progress label "0 / 360" and other hardcoded strings not going through i18n | `main.py:294,1315` | Low |

### 1.5 Performance

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 21 | GIF export does per-frame `ax.clear()` + full redraw 360 times, extremely slow (30-60 seconds); should use blitting or pre-rendering | `main.py:1338-1405` | High |
| 22 | GIF export retains all 360 PIL Images in memory (360-720 MB); may cause out of memory | `main.py:1327-1410` | Medium |

### 1.6 Testing and Engineering

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 23 | No i18n tests (key completeness, fallback behavior, format parameters) | `tests/` | Medium |
| 24 | No pressure angle rise/return phase tests | `tests/` | Medium |
| 25 | No cam profile tests with `sn=-1`/`pz=-1` (rotation/offset direction) | `tests/` | Medium |
| 26 | No `compute_full_motion` non-integer angle tests (e.g., 91+59+120+90); index rounding logic not covered | `tests/` | Medium |
| 27 | No `compute_anim_frame_data` boundary frame index tests (frame 0, frame N-1) | `tests/` | Medium |
| 28 | No `pyproject.toml`, no version number, no `conftest.py` | Project root | Medium |
| 29 | `requirements.txt` has no upper bounds; numpy 2.x may break compatibility | `requirements.txt` | Medium |
| 30 | No type annotations; static checking not possible | All files | Low |

---

## II. Optimization Directions

### Phase 1 — Fixes and Hardening (v0.2) ✅ Complete

- [x] **P1-1** Complete `requirements.txt`, add `Pillow` dependency
- [x] **P1-2** Fix cross-platform fonts: detect available Chinese fonts at runtime, auto-fallback
- [x] **P1-3** Fix cross-platform scroll wheel events: distinguish Windows / macOS / Linux `delta` values and event types
- [x] **P1-4** Fix window maximization compatibility: select `state('zoomed')` or `attributes('-fullscreen')` based on platform
- [x] **P1-5** Fix floating-point validation issue: convert angles to `int` in `_read_params` before passing to `validate_params`
- [x] **P1-6** Add `LICENSE` file (MIT)
- [x] **P1-7** Improve `.gitignore` (IDE directories, virtual environments, build artifacts, etc.)
- [x] **P1-8** Add unit tests for `cam_mechanics.py` (pytest, 59 tests all passing)

### Phase 2 — Refactoring and Performance (v0.3) ✅ Complete

- [x] **P2-2** Extract magic numbers into named constants or configuration items
- [x] **P2-3** Move GIF export to background thread + progress bar to avoid UI freezing
- [x] **P2-4** Eliminate duplicated follower drawing code between animation and GIF export; extract into shared function
- [x] **P2-5** Change static image export to direct recomputation and plotting, eliminating the `BlendedGenericTransform` hack
- [x] **P2-6** Support "Replay" button after animation finishes, without recomputation
- [x] **P2-7** Download filenames generated via i18n keys, switching with language
- [x] **P2-8** Extract color constants into a theme dictionary, preparing for dark mode
- [x] **P2-9** Move stdlib imports from method bodies to module top level
- [x] **P2-10** Eliminate static plot code duplication between `_plot_static` and `_on_download`

### Phase 3 — Correctness Fixes (v0.4) ✅ Complete

Goal: Fix critical issues affecting functional correctness, complete test coverage.

- [x] **P3-1** Fix `compute_full_motion` index rounding issue: add `i1/i2/i3` boundary checks, ensure `i3 <= N_POINTS`
- [x] **P3-2** Add four-angle sum validation to `compute_full_motion` (consistent with `validate_params`)
- [x] **P3-3** Add frame index range check to `compute_anim_frame_data`
- [x] **P3-4** Add try/except wrapping computation calls in `_on_start`; show friendly error instead of crash
- [x] **P3-5** Fix validation inconsistency between `validate_params` and computation engine: `e` must not be negative
- [x] **P3-6** Fix `error.unknown_law` format: use i18n key format instead of pipe format in `cam_mechanics.py`
- [x] **P3-7** Add user notification when `_read_params` truncates floating-point angles (e.g., "Angle 90.9 rounded to 90")
- [x] **P3-8** Add try/except error handling to `_export_excel` and `_on_download`
- [x] **P3-9** GIF export thread safety: add `threading.Lock` to protect `sim_data` reads
- [x] **P3-10** Complete tests: i18n key completeness, non-integer angle indexing, boundary frame index, `sn=-1`/`pz=-1` profiles, pressure angle rise/return

### Phase 4 — Performance Optimization (v0.5) ✅ Complete

Goal: Improve GIF export performance and memory efficiency.

- [x] **P4-1** GIF export: change to per-frame render + immediate stream write, avoid keeping 360 PIL Images in memory
- [x] **P4-2** GIF export: use blitting or pre-rendering optimization, reduce per-frame `ax.clear()` + full redraw overhead
- [x] **P4-3** Excel export: change to batch writing (`ws.append` row writes instead of per-cell)

### Phase 5 — Code Architecture (v0.6) ✅ Complete

Goal: Split large class, improve maintainability.

- [x] **P5-1** Split `CamSimulator` into independent modules:
  ```
  ui/
  ├── __init__.py     # Package init
  ├── constants.py    # Rendering constants and theme colors
  ├── drawing.py      # Shared drawing functions
  ├── params.py       # Parameter data model and random param generation
  └── plots.py        # Static chart plotting
  ```
- [x] **P5-2** Extract parameter data model class (`ParameterModel`), separate computation state from GUI state
- [x] **P5-3** Split `_build_gui` into `_build_sidebar`, `_build_toolbar`, `_build_figure` sub-methods

### Phase 6 — Feature Enhancement (v0.7) ✅ Complete

Goal: Expand simulation capabilities, improve engineering practicality.

- [x] **P6-1** Roller follower support: add roller radius parameter, compute actual profile (equidistant curve) and theoretical profile
- [x] **P6-2** Pressure angle curve chart: add independent chart showing pressure angle variation with rotation angle
- [x] **P6-3** Cam profile radius of curvature computation and display, marking minimum radius of curvature position
- [x] **P6-4** Parameter preset system: save/load common cam configurations (JSON file)
- [x] **P6-5** Configurable pressure angle threshold (sidebar input field)
- [x] **P6-6** Make `N_POINTS` configurable, supporting higher or lower discrete resolution

### Phase 7 — Experience Upgrade (v0.8) ✅ Complete

Goal: Polish interaction details, improve visual and operational experience.

- [x] **P7-1** Dark mode support (tkinter theme + matplotlib style switching)
- [x] **P7-2** Animation frame progress bar: display current frame/total frames, support drag-to-jump
- [x] **P7-3** Window resize adaptation: listen to `Configure` events to dynamically adjust Figure size
- [x] **P7-4** Real-time parameter input validation: show range errors as you type
- [x] **P7-5** Extended export formats: support SVG vector graphics, CSV data table export
- [x] **P7-6** i18n detail fixes: unify motion law suffix, internationalize Logo/progress labels

### Phase 8 — Engineering and Release (v1.0) ✅ Complete

Goal: Reach releasable quality, support convenient installation and distribution.

- [x] **P8-1** Add `pyproject.toml`, support `pip install camforge`
- [x] **P8-2** Add version number (`__version__`), display in window title
- [x] **P8-3** GitHub Actions CI: automatically run tests and code style checks (ruff)
- [x] **P8-4** Code coverage targets: `cam_mechanics.py` >= 90% (actual 95%), overall >= 70% (actual 95%)
- [x] **P8-5** Add type annotations, configure pyright static checking
- [x] **P8-6** Add upper bounds to `requirements.txt` to prevent breaking upgrades (e.g., numpy 2.x)
- [x] **P8-7** Maintain changelog (CHANGELOG.md)

### Phase 9 — v0.2 Modern UI and Performance (v0.2) ✅ Complete

Goal: Modernize UI layout, improve performance and maintainability.

- [x] **P9-1** New 2-row 4-column grid layout: Row 0 (Displacement | Velocity | Acceleration | Profile), Row 1 (Pressure Angle | Curvature | Animation | Info Panel)
- [x] **P9-2** Modular architecture: Extract `I18nManager`, `ThemeManager`, `ExportManager`, `SidebarBuilder`, `AnimationController` to `ui/` package
- [x] **P9-3** NumPy vectorization: `compute_roller_profile` and `compute_curvature_radius` use `np.roll`, 10x+ performance improvement
- [x] **P9-4** Widget caching for theme switching: Traverse cached control list instead of recursive tree traversal, 5x+ performance improvement
- [x] **P9-5** `ParameterModel` typed data model: Type-safe parameter passing with validation and conversion
- [x] **P9-6** Animation rendering extraction: `render_frame_artists` and `update_info_panel` pure functions in `ui/animation.py`
- [x] **P9-7** GIF generation extraction: `generate_gif_frames` independent function with progress callback
- [x] **P9-8** Windows standalone executable: PyInstaller packaging with icon, 70 MB single file

### Phase 10 — v0.3 Simplified Layout (v0.3) ✅ Complete

Goal: Simplify layout, merge related charts.

- [x] **P10-1** v0.3.0: Triple Y-axis motion curves (displacement/velocity/acceleration combined)
- [x] **P10-2** v0.3.1: Dual Y-axis geometry constraints (pressure angle/curvature radius combined)
- [x] **P10-3** Remove static profile plot (profile still shown in animation)
- [x] **P10-4** Simplify layout to 2x2 grid: static charts on top, dynamic on bottom

### Phase 11 — v0.3.2 Left-Right Split Layout ✅ Complete

Goal: Optimize animation display area.

- [x] **P11-1** Left-right split: left side (motion curves + geometry constraints), right side (animation + info panel)
- [x] **P11-2** Larger animation area, info panel moved to right edge
- [x] **P11-3** GridSpec 2x3 with width_ratios [1, 1.6, 0.4]

### Phase 12 — v0.4.0 Layout Optimization and i18n Improvements ✅ Complete

Goal: Optimize layout spacing, improve internationalization support.

- [x] **P12-1** Three-column layout: static charts | spacer | animation, width_ratios [1, 0.25, 0.9]
- [x] **P12-2** Increase second right Y-axis offset for motion curves (45→60 pixels)
- [x] **P12-3** Two-row status bar: Row 1 for status message, Row 2 for stroke/initial displacement/max pressure angle
- [x] **P12-4** Button order adjustment: Load Preset → Save Preset → Download
- [x] **P12-5** CSV/SVG/preset filename i18n (Chinese filenames in Chinese mode)
- [x] **P12-6** Plain text labels for status bar (avoid LaTeX symbol display issues)

### Phase 13 — v0.4.1 Bug Fixes and Optimizations ✅ Complete

Goal: Fix n_points related bugs, optimize display quality.

- [x] **P13-1** Fix `compute_full_motion` index scaling: `i = angle_deg * (n_points / 360)`
- [x] **P13-2** Fix animation frame angle scaling: cam rotation, normal/tangent calculations
- [x] **P13-3** `n_points` now passed as function parameter, no global variable modification
- [x] **P13-4** GIF export fixes: equal aspect ratio, roller data passing
- [x] **P13-5** Curvature radius interference warning uses absolute value comparison
- [x] **P13-6** Roller visualization line width matches cam profile (linewidth=2)
- [x] **P13-7** Download option "廓形" changed to "廓形图" (Profile → Profile Plot)
- [x] **P13-8** Speed slider label and slider horizontally aligned
- [x] **P13-9** Spline interpolation for smooth display when n_points < 180

### Phase 14 — v0.4.2 Code Cleanup ✅ Complete

Goal: Clean up redundant files and code, improve code quality.

- [x] **P14-1** Remove duplicate icon file `CamForge.ico` (keep `camforge.ico`)
- [x] **P14-2** Remove auto-generated `CamForge-v0.4.1.spec`
- [x] **P14-3** Remove unused imports in `main.py`: `BytesIO`, `compute_rotated_cam`, `compute_anim_frame_data`, `compute_pressure_angle_arc`
- [x] **P14-4** Remove unused variables in `cam_mechanics.py`: `delta_01`, `delta_02`
- [x] **P14-5** Fix line length issues in `i18n.py` (split long strings)
- [x] **P14-6** Reorganize imports in `main.py` (sorted, grouped)
- [x] **P14-7** Update `.gitignore` to ignore auto-generated spec files

### Phase 15 — v0.4.3 Seventh-Order Polynomial Motion Law ✅ Complete

Goal: Add seventh-order polynomial motion law (4-5-6-7 polynomial).

- [x] **P15-1** Add law=6 seventh-order polynomial calculation to `compute_rise()`
- [x] **P15-2** Add law=6 seventh-order polynomial calculation to `compute_return()`
- [x] **P15-3** Update motion law validation from (1,2,3,4,5) to (1,2,3,4,5,6)
- [x] **P15-4** Update error messages from "law must be 1-5" to "law must be 1-6"
- [x] **P15-5** Add i18n translations: `law.6`, `law.combo.6`
- [x] **P15-6** Update `get_motion_law_list()` to return 6 options
- [x] **P15-7** Add law=6 unit tests: boundary conditions, smoothness comparison
- [x] **P15-8** Update README.md and README.en.md motion law tables
- [x] **P15-9** Update CHANGELOG.md with v0.4.3 entry

---

## III. Issue Statistics

```
Severity distribution:
  High  ██████░░░░  3 items  (thread safety, index out of bounds, GIF performance)
  Medium  ██████████████████  18 items  (validation inconsistency, error handling, test gaps, memory, etc.)
  Low  ████████░░░░░░  8 items  (i18n details, hardcoded values, type annotations, etc.)
```

---

## IV. Priority Principles

1. **Correctness First** — Issues affecting functional results (index out of bounds, thread safety, validation inconsistency) take priority over experience issues
2. **Testability First** — Adding tests for pure computation modules is the safety net for all subsequent refactoring
3. **Performance Next** — GIF export taking 30-60 seconds and 720 MB memory are user-perceivable severe issues
4. **Incremental Refactoring** — When splitting large classes, preserve functionality; each step should be independently verifiable
5. **i18n Consistency** — All user-visible strings must go through i18n, including error messages and formatting details
