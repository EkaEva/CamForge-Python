# Changelog

All notable changes to CamForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
