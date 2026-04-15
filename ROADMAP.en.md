[中文](ROADMAP.md) | English | [日本語](ROADMAP.ja.md)

# CamForge Roadmap

> Current status analysis and future optimization directions

---

## I. Existing Issues

### 1.1 Dependency Management

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 1 | `Pillow` is imported in `main.py:884` for GIF export but not listed in `requirements.txt` | `requirements.txt` / `main.py:884` | High |
| 2 | No version lock file (`Pipfile` / `poetry.lock`); different environments may produce compatibility differences | Project root | Medium |
| 3 | No `setup.py` / `pyproject.toml`; project cannot be installed as a package | Project root | Low |

### 1.2 Code Quality

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 4 | `CamSimulator` class exceeds **1000 lines**; GUI construction, computation, animation, and export logic are all coupled in one class | `main.py:56-1027` | High |
| 5 | `_on_download` method is approximately **160 lines**; static image export and GIF generation logic are mixed, and imports (`PIL`, `os`, `BytesIO`) are done inside the method | `main.py:816-976` | High |
| 6 | The `save_static` closure for static image export copies graphics by iterating `ax.get_lines()`, with special `BlendedGenericTransform` handling for `axvline` — fragile and unmaintainable | `main.py:840-870` | Medium |
| 7 | Magic numbers scattered throughout: `r_0 * 0.04` (tip half-width), `r_0 * 0.08` (tip height), `r_0 * 4` (rod length), `r_0 * 3` (upper/lower limit line width), `r_0 * 0.3` (arc radius), `30` (pressure angle threshold), etc. | `main.py:735-768` | Medium |
| 8 | `generate_random_params` uses a `while True` loop to generate random parameters; in extreme cases it may loop for a long time | `main.py:30-36` | Low |
| 9 | Animation frame data is computed once in `_animate_frame` and once in GIF export; follower drawing logic is completely duplicated | `main.py:734-744` vs `main.py:929-934` | Medium |

### 1.3 Functional Defects

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 10 | Animation cannot be replayed after finishing; must click "Start Simulation" to recompute | `main.py:690-699` | Medium |
| 11 | UI completely freezes during GIF export (synchronous sequential rendering of 360 frames) with no progress feedback | `main.py:915-973` | High |
| 12 | Download filenames are hardcoded in Chinese (`位移曲线.png`, `凸轮廓形.png`), which may cause garbled text on non-Chinese systems | `main.py:874-880` | Medium |
| 13 | Static curves (displacement/velocity/acceleration) do not display the currently selected motion law name | `main.py:480-518` | Low |
| 14 | Pressure angle threshold of 30° is hardcoded; different applications (e.g., high-speed cams) may require different thresholds | `main.py:436` | Low |
| 15 | `validate_params` requires four angles to be integers, but `_read_params` first converts to `float` then validates integrality; floating-point precision may cause false negatives | `main.py:361-393` / `cam_mechanics.py:469` | Medium |

### 1.4 User Experience

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 16 | Parameter inputs have no default values; all input fields are empty on first launch | `main.py:129-161` | Medium |
| 17 | No parameter preset/template feature; common cam configurations cannot be saved and reused | — | Medium |
| 18 | Sidebar scrolling only supports Windows `MouseWheel` events; macOS/Linux trackpads and scroll wheels are unresponsive | `main.py:109-110` | Medium |
| 19 | Chart layout does not adapt on window resize (`Figure` size is fixed) | `main.py:306` | Low |
| 20 | Error/warning messages are only displayed as red text in the status bar; no popup or more prominent notification | `main.py:296-298` | Low |
| 21 | No keyboard shortcuts (e.g., Enter to start simulation, Space to pause/resume) | — | Low |

### 1.5 Cross-platform Compatibility

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 22 | Fonts hardcoded to `SimHei` / `Microsoft YaHei` (Windows Chinese fonts); macOS/Linux do not have these by default | `main.py:24` | High |
| 23 | `root.state('zoomed')` maximization only works reliably on Windows; macOS requires `attributes('-fullscreen', True)` | `main.py:63` | Medium |
| 24 | Mouse scroll wheel event `event.delta / 120` follows Windows conventions; Linux/macOS values differ | `main.py:335` | Medium |

### 1.6 Testing and Engineering

| # | Issue | Location | Severity |
|---|------|------|:--------:|
| 25 | No test cases at all; the pure function logic in `cam_mechanics.py` is fully testable but not covered | — | High |
| 26 | No CI/CD configuration | — | Medium |
| 27 | No `LICENSE` file (README states MIT but the actual file is missing) | — | Medium |
| 28 | No IDE configuration exclusions in `.gitignore` (`.vscode/`, `.idea/`, etc.) | `.gitignore` | Low |

---

## II. Optimization Directions

### Phase 1 — Fixes and Hardening (v0.2)

Goal: Resolve critical issues affecting functional correctness and cross-platform usability.

- [x] **P1-1** Complete `requirements.txt`, add `Pillow` dependency
- [x] **P1-2** Fix cross-platform fonts: detect available Chinese fonts at runtime, auto-fallback
- [x] **P1-3** Fix cross-platform scroll wheel events: distinguish Windows / macOS / Linux `delta` values and event types
- [x] **P1-4** Fix window maximization compatibility: select `state('zoomed')` or `attributes('-fullscreen')` based on platform
- [x] **P1-5** Fix floating-point validation issue: convert angles to `int` in `_read_params` before passing to `validate_params`
- [x] **P1-6** Add `LICENSE` file (MIT)
- [x] **P1-7** Improve `.gitignore` (IDE directories, virtual environments, build artifacts, etc.)
- [x] **P1-8** Add unit tests for `cam_mechanics.py` (pytest, 59 tests all passing):
  - Boundary values and continuity for five motion laws
  - Cam profile closure (first and last coordinates match)
  - Pressure angle computation correctness
  - Parameter validation covering all branches

### Phase 2 — Refactoring and Performance (v0.3)

Goal: Improve code structure, enhance animation performance and export experience.

- [ ] **P2-1** Split `CamSimulator` into independent modules:
  ```
  ui/
  ├── sidebar.py      # Sidebar construction and parameter management
  ├── toolbar.py      # Toolbar buttons and controls
  ├── plots.py        # Static chart plotting
  ├── animation.py    # Animation control and frame rendering
  ├── export.py       # Image/GIF export
  └── app.py          # Main window assembly and launch
  ```
- [x] **P2-2** Extract magic numbers into named constants or configuration items:
  ```python
  TIP_WIDTH_RATIO = 0.04
  TIP_HEIGHT_RATIO = 0.08
  ROD_LENGTH_RATIO = 4.0
  ARC_RADIUS_RATIO = 0.3
  MAX_PRESSURE_ANGLE = 30.0
  ```
- [x] **P2-3** Move GIF export to background thread + progress bar to avoid UI freezing
- [x] **P2-4** Eliminate duplicated follower drawing code between animation and GIF export; extract into shared function
- [x] **P2-5** Change static image export to direct recomputation and plotting (instead of copying `ax.get_lines()`), eliminating the `BlendedGenericTransform` hack
- [x] **P2-6** Support "Replay" button after animation finishes, without recomputation
- [x] **P2-7** Use English filenames for downloads (displacement.png / velocity.png / cam_profile.png / cam_animation.gif)

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

### Phase 4 — Experience Upgrade (v0.5)

Goal: Polish interaction details, improve visual and operational experience.

- [ ] **P4-1** Dark mode support (tkinter theme + matplotlib style switching)
- [ ] **P4-2** Chart interaction enhancement: mouse hover to display values, zoom/pan, click to navigate to corresponding animation frame
- [ ] **P4-3** Animation frame progress bar: display current frame/total frames, support drag-to-jump
- [ ] **P4-4** Window resize adaptation: listen to `Configure` events to dynamically adjust Figure size
- [ ] **P4-5** Real-time parameter input validation: show range errors as you type, rather than only reporting errors after clicking "Start"
- [ ] **P4-6** Multi-language support (i18n): Chinese/English interface switching
- [ ] **P4-7** Extended export formats: support SVG vector graphics, CSV data table export
- [ ] **P4-8** Cam 3D visualization preview (optional, based on matplotlib 3D or PyOpenGL)

### Phase 5 — Engineering and Release (v1.0)

Goal: Reach releasable quality, support convenient installation and distribution.

- [ ] **P5-1** Add `pyproject.toml`, support `pip install camforge`
- [ ] **P5-2** GitHub Actions CI: automatically run tests and code style checks (ruff / black)
- [ ] **P5-3** PyPI release workflow
- [ ] **P5-4** Package as desktop application (PyInstaller / Nuitka), provide Windows / macOS installers
- [ ] **P5-5** Online documentation (GitHub Pages): user guide, algorithm principles, API documentation
- [ ] **P5-6** Maintain changelog (CHANGELOG.md)
- [ ] **P5-7** Code coverage targets: `cam_mechanics.py` >= 90%, overall >= 70%

---

## III. Issue Statistics

```
Severity distribution:
  High  ████████░░  6 items  (Missing dependency, oversized class, UI freeze, no tests, cross-platform fonts, export coupling)
  Medium  ██████████████░░  11 items  (Magic numbers, duplicated logic, filename garbling, floating-point validation, etc.)
  Low  ████████░░  7 items  (Hardcoded threshold, no shortcuts, no defaults, etc.)
```

---

## IV. Priority Principles

1. **Correctness First** — Issues affecting functional results (missing dependencies, floating-point validation) take priority over experience issues
2. **Cross-platform First** — Font and event compatibility directly determines whether macOS/Linux users can use the application normally
3. **Testability First** — Adding tests for pure computation modules is the safety net for all subsequent refactoring
4. **Incremental Refactoring** — When splitting large classes, preserve functionality; each step should be independently verifiable
5. **User Perception First** — Issues that directly impact user experience (UI freezing, no progress feedback) should be resolved as early as possible
