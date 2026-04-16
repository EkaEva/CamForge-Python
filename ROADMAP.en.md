[中文](ROADMAP.md) | English | [日本語](ROADMAP.ja.md)

# CamForge Roadmap

> Current status analysis and future optimization directions

---

## I. Existing Issues

### 1.1 Code Architecture

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 1 | `CamSimulator` class exceeds **1390 lines**; GUI construction, computation, animation, export, and i18n logic are all coupled | `main.py` | High |
| 2 | `_build_gui` method is ~**300 lines**; sidebar/toolbar/chart layout all inline | `main.py:218-522` | High |
| 3 | Static plot code is duplicated between `_plot_static` and `_on_download` | `main.py:698-782` vs `1116-1214` | Medium |
| 4 | Follower drawing logic is still duplicated between `_animate_frame` and GIF export | `main.py:1000-1010` vs `1368-1371` | Medium |
| 5 | Color values scattered as string literals (`'#f8fafc'`, `'#2563eb'`, etc.), not extracted as theme constants | `main.py` multiple | Medium |
| 6 | Stdlib modules imported inside methods (`os`, `threading`, `BytesIO`, `filedialog`) | `main.py:1093-1095` etc. | Low |

### 1.2 Robustness

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 7 | GIF export thread reads `sim_data` without locking; mid-export re-simulation may cause data inconsistency | `main.py:1332` | Medium |
| 8 | `_export_excel` `wb.save()` has no try/except; crashes on disk full or invalid path | `main.py:1280` | Medium |
| 9 | `fig.savefig()` calls in `_on_download` have no error handling | `main.py:1116-1214` | Medium |
| 10 | Keyboard shortcut `R` is globally bound; cannot type 'r' in Entry fields | `main.py:145` | Medium |
| 11 | Status bar warning overwrite: pressure angle and stroke warnings both trigger but only the latter is visible | `main.py:666-672` | Medium |
| 12 | `_on_close` does not wait for GIF export thread; may interrupt export | `main.py:1488-1491` | Low |
| 13 | `generate_random_params` has no iteration safety limit | `main.py:80-86` | Low |

### 1.3 Computation Engine

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 14 | `compute_rise`/`compute_return` divide by zero when `delta_0=0` or `omega=0`; no internal guards | `cam_mechanics.py` | Medium |
| 15 | `compute_cam_profile` produces NaN from `sqrt` when `e > r_0`; no protective check | `cam_mechanics.py:252` | Medium |
| 16 | `compute_pressure_angle` divides by zero when `s_0 + s = 0` (floating-point `e ≈ r_0`) | `cam_mechanics.py:286` | Medium |
| 17 | Constant accel/decel law (law 2) midpoint misaligns with discrete grid when `delta_0` is odd | `cam_mechanics.py:37-55` | Low |
| 18 | `N_POINTS = 360` hardcoded; resolution not adjustable | `cam_mechanics.py:8` | Low |
| 19 | Pressure angle arc drawing threshold `0.5°` hardcoded | `cam_mechanics.py:425` | Low |

### 1.4 Internationalization

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 20 | Static plot titles use Chinese parentheses `（）`; should use `()` in English/Japanese | `main.py:720` | Low |
| 21 | Excel sheet name "CamForge" hardcoded, not i18n | `main.py:1250` | Low |
| 22 | openpyxl missing error message hardcoded in English | `main.py:1237` | Low |
| 23 | Motion law combobox Chinese "规律" suffix inconsistent (laws 1/2 omit, 3/4/5 include) | `i18n.py:law.combo.*` | Low |

### 1.5 Testing and Engineering

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 24 | No i18n tests (key completeness, fallback behavior) | `tests/` | Medium |
| 25 | No pressure angle rise/return phase tests | `tests/` | Medium |
| 26 | No cam profile tests with `sn=-1`/`pz=-1` (rotation/offset direction) | `tests/` | Medium |
| 27 | No GUI integration tests | `tests/` | Low |
| 28 | No `pyproject.toml`, no `conftest.py`, no `pytest-cov` | Project root | Medium |
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

### Phase 2 — Refactoring and Performance (v0.3)

Goal: Improve code structure, enhance animation performance and export experience.

- [ ] **P2-1** Split `CamSimulator` into independent modules:
  ```
  ui/
  ├── sidebar.py      # Sidebar construction and parameter management
  ├── toolbar.py      # Toolbar buttons and controls
  ├── plots.py        # Static chart plotting
  ├── animation.py    # Animation control and frame rendering
  ├── export.py       # Image/GIF/Excel export
  └── app.py          # Main window assembly and launch
  ```
- [x] **P2-2** Extract magic numbers into named constants or configuration items
- [x] **P2-3** Move GIF export to background thread + progress bar to avoid UI freezing
- [x] **P2-4** Eliminate duplicated follower drawing code between animation and GIF export; extract into shared function
- [x] **P2-5** Change static image export to direct recomputation and plotting, eliminating the `BlendedGenericTransform` hack
- [x] **P2-6** Support "Replay" button after animation finishes, without recomputation
- [x] **P2-7** Download filenames generated via i18n keys, switching with language
- [x] **P2-8** Extract color constants into a theme dictionary, preparing for dark mode
- [x] **P2-9** Move stdlib imports from method bodies to module top level
- [x] **P2-10** Eliminate static plot code duplication between `_plot_static` and `_on_download`

### Phase 3 — Feature Enhancement (v0.4)

Goal: Expand simulation capabilities, improve engineering practicality.

- [ ] **P3-1** Roller follower support: add roller radius parameter, compute actual profile (equidistant curve) and theoretical profile
- [ ] **P3-2** Oscillating follower support: support oscillating follower plate cam mechanisms
- [ ] **P3-3** Pressure angle curve chart: add independent chart showing pressure angle variation with rotation angle
- [ ] **P3-4** Cam profile radius of curvature computation and display, marking minimum radius of curvature position
- [ ] **P3-5** Parameter preset system: save/load common cam configurations (JSON file)
- [x] **P3-6** Fill input fields with default values, lowering the barrier for first-time use
- [x] **P3-7** Keyboard shortcuts: Enter to start, Space to pause/resume/replay, R for random
- [x] **P3-8** Display current motion law name in static curve chart titles
- [ ] **P3-9** Configurable pressure angle threshold (sidebar input field or dropdown)
- [x] **P3-10** Defensive programming in computation engine: add parameter validity assertions inside `compute_*` functions
- [ ] **P3-11** Make `N_POINTS` configurable, supporting higher or lower discrete resolution

### Phase 4 — Experience Upgrade (v0.5)

Goal: Polish interaction details, improve visual and operational experience.

- [ ] **P4-1** Dark mode support (tkinter theme + matplotlib style switching)
- [ ] **P4-2** Chart interaction enhancement: mouse hover to display values, zoom/pan, click to navigate to corresponding animation frame
- [ ] **P4-3** Animation frame progress bar: display current frame/total frames, support drag-to-jump
- [ ] **P4-4** Window resize adaptation: listen to `Configure` events to dynamically adjust Figure size
- [ ] **P4-5** Real-time parameter input validation: show range errors as you type, rather than only reporting errors after clicking "Start"
- [x] **P4-6** Multi-language support (i18n): Chinese/English/Japanese runtime switching
- [ ] **P4-7** Extended export formats: support SVG vector graphics, CSV data table export
- [ ] **P4-8** Cam 3D visualization preview (optional, based on matplotlib 3D or PyOpenGL)
- [x] **P4-9** Keyboard shortcut focus awareness: suppress single-key shortcuts when Entry has focus
- [x] **P4-10** Accumulate multiple status bar warnings instead of overwriting
- [x] **P4-11** "Clear Params" should restore defaults instead of leaving blanks
- [x] **P4-12** Fix i18n details: Chinese→English parentheses, Excel sheet name/error message i18n

### Phase 5 — Engineering and Release (v1.0)

Goal: Reach releasable quality, support convenient installation and distribution.

- [ ] **P5-1** Add `pyproject.toml`, support `pip install camforge`
- [ ] **P5-2** GitHub Actions CI: automatically run tests and code style checks (ruff / black)
- [ ] **P5-3** PyPI release workflow
- [ ] **P5-4** Package as desktop application (PyInstaller / Nuitka), provide Windows / macOS installers
- [ ] **P5-5** Online documentation (GitHub Pages): user guide, algorithm principles, API documentation
- [ ] **P5-6** Maintain changelog (CHANGELOG.md)
- [ ] **P5-7** Code coverage targets: `cam_mechanics.py` >= 90%, overall >= 70%
- [ ] **P5-8** Add type annotations, configure mypy/pyright static checking
- [ ] **P5-9** Add upper bounds to `requirements.txt` to prevent breaking upgrades (e.g., numpy 2.x)
- [ ] **P5-10** Expand tests: i18n key completeness, pressure angle rise/return, rotation/offset direction profiles

---

## III. Issue Statistics

```
Severity distribution:
  High  ████░░░░░░  2 items  (monolithic class, long method)
  Medium  ████████████████░░  16 items  (code duplication, thread safety, error handling, test gaps, etc.)
  Low  ██████████░░░░░░  10 items  (i18n details, hardcoded thresholds, type annotations, etc.)
```

---

## IV. Priority Principles

1. **Correctness First** — Issues affecting functional results (division by zero, thread safety, error handling) take priority over experience issues
2. **Testability First** — Adding tests for pure computation modules is the safety net for all subsequent refactoring
3. **Incremental Refactoring** — When splitting large classes, preserve functionality; each step should be independently verifiable
4. **User Perception First** — Issues that directly impact user experience (shortcut conflicts, warning overwrites) should be resolved as early as possible
5. **i18n Consistency** — All user-visible strings must go through i18n, including error messages and formatting details
