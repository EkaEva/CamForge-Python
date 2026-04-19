# Changelog

All notable changes to CamForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2026-04-19

### Added
- Seventh-order polynomial motion law (4-5-6-7 polynomial) as law=6
  - Formula: $s = h(35t^4 - 84t^5 + 70t^6 - 20t^7)$
  - Zero velocity and acceleration at both boundaries (smoother than quintic)
- i18n translations for law 6: `law.6`, `law.combo.6`
- Tests for law 6: boundary conditions, smoothness comparison with quintic

### Changed
- Motion law validation now accepts laws 1-6 (was 1-5)
- Error messages updated from "law must be 1-5" to "law must be 1-6"
- Motion law dropdown now shows 6 options

## [0.4.2] - 2026-04-19

### Changed
- Reorganize imports in `main.py` (sorted, remove unused)
- Fix line length issues in `i18n.py` (split long strings)

### Removed
- Duplicate `CamForge.ico` (kept `camforge.ico`)
- Auto-generated `CamForge-v0.4.1.spec` (use `CamForge.spec` instead)
- Unused imports in `main.py`: `BytesIO`, `compute_rotated_cam`, `compute_anim_frame_data`, `compute_pressure_angle_arc`
- Unused variables in `cam_mechanics.py`: `delta_01`, `delta_02`

### Fixed
- Add `CamForge-v*.spec` to `.gitignore` to prevent future auto-generated spec files from being committed

## [0.4.1] - 2026-04-18

### Added
- Spline interpolation for smooth cam profile display when `n_points < 180`
- `smooth_closed_curve()` function using scipy `splprep`/`splev` for periodic curves
- `n_points` parameter to `compute_full_motion()` and `compute_anim_frame_data()` functions

### Changed
- Roller follower visualization: line width now matches cam profile (linewidth=2)
- Download checkbox label changed from "廓形" to "廓形图" (Profile → Profile Plot)
- Speed slider label and slider are now horizontally aligned
- `n_points` is now passed as function parameter instead of modifying global variable

### Fixed
- Phase boundary indices now correctly scaled by `n_points/360`
- Animation frame angles now correctly scaled by `n_points/360`
- GIF export aspect ratio: circles no longer appear as ellipses
- GIF export now correctly shows roller follower (was missing `r_r`, `x_actual`, `y_actual` data)
- Curvature radius interference warning now uses absolute value (was comparing negative values)
- Info panel angle display correctly shows actual angle, not frame index

## [0.4.0] - 2026-04-18

### Added
- Three-column GridSpec layout with spacer between static plots and animation
- i18n keys for SVG and preset filenames: `export.filename.svg`, `export.filename.preset`
- Plain text labels for status bar: `status.label.h`, `status.label.s0`, `status.label.max_alpha`

### Changed
- Layout optimized with width_ratios [1, 0.25, 0.9] for better Y-axis spacing
- Increased outward offset for second right Y-axis from 45 to 60 pixels
- Status bar reorganized into two rows:
  - Row 1: status message only
  - Row 2: stroke | initial displacement | max pressure angle
- Button order changed: Load Preset → Save Preset → Download
- Info panel width increased from 0.22 to 0.28 (in animation)

### Fixed
- CSV filename and header now use i18n (Chinese: 凸轮数据.csv with Chinese headers)
- SVG filename now uses i18n (Chinese: 凸轮综合图.svg)
- Preset filename now uses i18n (Chinese: 凸轮预设.json)
- LaTeX symbols no longer show as raw text in status bar labels

## [0.3.3] - 2026-04-18

### Added
- New download checkbox layout with 8 options in 2 rows:
  - Row 1: 运动线图 | 廓形 | CSV | Excel
  - Row 2: 几何约束 | 动画 | SVG | 预设
- Preset save in download: saves current parameters as JSON file
- Excel export now includes 7 columns: 转角, 向径, 推杆位移, 推杆速度, 推杆加速度, 曲率半径, 压力角
- CSV export now includes curvature radius column
- i18n keys: `toolbar.cb.dl_motion`, `toolbar.cb.dl_geom`, `toolbar.cb.dl_preset`
- i18n keys: `export.filename.motion`, `export.filename.geometry`
- i18n keys: `excel.col.displacement`, `excel.col.curvature`, `excel.col.pressure_angle`

### Changed
- Download section reorganized to match static plot layout (motion curves + geometry constraints)
- SVG export now shows motion curves and geometry constraints side by side
- ExportManager simplified to handle new combined plots

## [0.3.2] - 2026-04-18

### Changed
- New layout: left-right split with 2x3 grid
  - Left column: motion curves (top) | geometry constraints (bottom)
  - Right side: animation (main area, spans 2 rows) | info panel (right edge, spans 2 rows)
- GridSpec width_ratios [1, 1.8, 0.35], wspace=0.40 for better spacing
- Animation area larger, info panel on right edge

### Fixed
- Adjusted wspace and width_ratios to prevent triple Y-axis from overlapping with animation area

## [0.3.1] - 2026-04-18

### Added
- New layout: top-bottom split with 2x1 grid
  - Top row: motion curves (left) | geometry constraints (right)
  - Bottom row: animation (left) | info panel (right)
- Dual Y-axis geometry constraints plot: pressure angle (left, red solid) + curvature radius (right, blue dashed)
- `draw_geometry_constraints()` function in `ui/plots.py`
- i18n keys: `plot.title.geometry_constraints`, `plot.legend.pressure_angle`, `plot.legend.curvature`

### Removed
- Cam profile plot removed from static charts (profile still shown in animation)

### Changed
- Simplified layout from 2x4 to 2x2 GridSpec
- `_plot_static()` now uses `ax_geom` for combined geometry constraints

## [0.3.0] - 2026-04-18

### Added
- New layout: left-right split with 2x2 static plots on left, animation + info panel on right
- Triple Y-axis motion curve plot: displacement (left, red solid), velocity (right, blue dashed), acceleration (right, green dash-dot)
- `draw_motion_curves()` function in `ui/plots.py` for combined motion visualization
- i18n keys: `plot.title.motion`, `plot.legend.displacement`, `plot.legend.velocity`, `plot.legend.acceleration`

### Changed
- Layout restructured: left side (motion curves | pressure angle, curvature | profile), right side (info panel | animation)
- GridSpec changed from 2x4 equal columns to width_ratios=[1, 1, 0.6, 1.4]
- Info panel now spans two rows, positioned left of animation
- `_plot_static()` updated to use new `ax_motion` for triple Y-axis plot

## [0.2.0] - 2026-04-18

### Added
- Modern 2-row 4-column grid layout for widescreen optimization
- Row 1: Displacement | Velocity | Acceleration | Cam Profile
- Row 2: Pressure Angle | Curvature Radius | Animation | Info Panel
- Adaptive scaling on window resize, no clipping or white space
- Modular architecture with composition pattern:
  - `I18nManager` for internationalization
  - `ThemeManager` for theme switching with widget caching
  - `ExportManager` for all export formats
  - `SidebarBuilder` for parameter panel construction
  - `AnimationController` for animation state and frame scheduling
- NumPy vectorization in `compute_roller_profile` and `compute_curvature_radius` using `np.roll`
- Widget caching for theme switching (5x+ performance improvement)
- `ParameterModel` typed data model with validation and conversion
- Pure function extraction: `render_frame_artists` and `update_info_panel` in `ui/animation.py`
- GIF generation extraction: `generate_gif_frames` with progress callback
- Windows standalone executable via PyInstaller (~70 MB single file)
- Unit tests expanded to 136 tests

### Changed
- Layout restructured from stacked panels to 2-row 4-column grid
- Axis assignments updated: `ax_profile` → `ax_p`, new positions for all charts
- Technical architecture refactored: `CamSimulator` delegates to manager classes
- `ui/` package reorganized: `animation.py`, `constants.py`, `drawing.py`, `export.py`, `i18n_manager.py`, `params.py`, `plots.py`, `sidebar.py`, `theme.py`
- README.md and README.en.md updated with v0.2 layout diagram and architecture
- ROADMAP.md and ROADMAP.en.md updated with Phase 9 (v0.2)

### Improved
- Animation rendering performance with pure function extraction
- Theme switching performance with widget list caching
- Code maintainability with modular architecture
- Export reliability with folder parameter passing (no double filedialog popup)

### Fixed
- Download dialog double-popup bug (filedialog called only once)
- Layout clipping on right and bottom edges (manual aspect ratio calculation)
- Bottom row x-axis label clipping (GridSpec bottom margin adjusted to 0.08)

## [0.1.0] - 2026-04-17

### Added
- Complete GUI application with tkinter + matplotlib
- Five motion laws: uniform, constant accel/decel, simple harmonic, cycloidal, quintic polynomial
- Cam profile computation with offset follower support
- Pressure angle computation and visualization
- Curvature radius computation with minimum marking
- Roller follower support: actual profile (equidistant curve) computation
- Pressure angle curve chart
- Curvature radius curve chart
- Animation with real-time follower, tangent, normal, and pressure angle arc display
- GIF animation export with progress bar
- Static image export (TIFF, SVG)
- Excel data export with openpyxl
- CSV data table export
- Parameter preset system: save/load JSON configurations
- Configurable pressure angle threshold
- Configurable N_POINTS (discrete resolution)
- Dark mode support (tkinter theme + matplotlib style switching)
- Animation frame progress bar with drag-to-seek
- Window resize adaptation
- Real-time parameter input validation
- i18n: Chinese (zh) and English (en) full support
- Cross-platform compatibility (Windows, macOS, Linux)
- `pyproject.toml` for pip-installable package
- Version number displayed in window title
- GitHub Actions CI workflow (test + ruff lint, multi-OS/multi-Python)
- Type annotations for `cam_mechanics.py` with pyright config
- `requirements.txt` with upper bounds to prevent breaking upgrades
- Unit tests: 136 tests, 95% overall coverage
- MIT License

### Fixed
- Index rounding boundary protection in `compute_full_motion`
- Four-angle sum validation in computation engine
- Frame index range check in `compute_anim_frame_data`
- Thread-safe `sim_data` access with `threading.Lock` during GIF export
- Validation consistency: `e` must not be negative
- `error.unknown_law` format using plain string instead of pipe format
- Float truncation warning when angle inputs are non-integer
- Error handling in `_on_start`, `_export_excel`, `_on_download`
- Cross-platform font detection and fallback
- Cross-platform scroll wheel event handling
- Window maximization compatibility across platforms

### Changed
- GIF export uses frame-by-frame rendering with `optimize=True` for memory efficiency
- Excel export uses batch `ws.append()` row writes
- Code architecture: split into `ui/` package (constants, drawing, params, plots)
- `_build_gui` split into `_build_sidebar`, `_build_toolbar`, `_build_figure`
- Extracted `ParameterModel` data class and `generate_random_params()`
- Extracted rendering constants and theme dictionaries
- All user-visible strings go through i18n system

## [0.0.1] - 2025-04-01

### Added
- Initial release: basic cam mechanism simulation with tkinter GUI
- Displacement, velocity, acceleration curves
- Cam profile plot
- Animation playback
- Chinese/English language support
