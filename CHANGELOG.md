# Changelog

All notable changes to CamForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-17

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

## [0.1.0] - 2025-04-01

### Added
- Initial release: basic cam mechanism simulation with tkinter GUI
- Displacement, velocity, acceleration curves
- Cam profile plot
- Animation playback
- Chinese/English language support
