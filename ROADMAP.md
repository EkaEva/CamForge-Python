[中文](ROADMAP.md) | English

# CamForge Roadmap

> ⚠️ **项目已迁移 / Project Moved**
>
> 本项目已停止维护，后续开发已迁移至新仓库：
>
> **新仓库地址：[https://github.com/EkaEva/CamForge-Next](https://github.com/EkaEva/CamForge-Next)**
>
> 新版本包含架构重构、平底从动件支持、逆向设计功能等重大更新。
> 本 ROADMAP 中的 v0.7.0 开发计划将在新项目中继续推进。
>
> ---

> Current status analysis and future optimization directions

---

## I. Existing Issues (Updated for v0.6.13)

### 1.1 Code Architecture

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 1 | `CamSimulator` 仍然是 **1094 行**的 God Class，GUI 构建、仿真管线、导出调度、动画控制逻辑全部耦合 | `main.py` | High | Open |
| 2 | `_on_start` 方法 **110 行**（407-516），参数校验 → 计算 → 缓存 → 绘图 → 启动动画全部内联，无法独立测试 | `main.py:407-516` | High | Open |
| 3 | `sim_data` 是原始 dict（含 22+ key），无类型安全，拼写错误无编译期检测 | `main.py:494-508` | Medium | Open |
| 4 | `_build_gui` / `_on_language_change` / `_on_theme_change` 中回调函数列表重复手写 3 次（11 个 callback），修改极易遗漏 | `main.py:193-198, 277-297, 214-227` | Medium | Open |
| 5 | `_do_export` 直接调用 `export_mgr._export_excel`（访问私有方法），违反封装 | `main.py:656` | Low | Open |

### 1.2 Robustness

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 6 | GIF 导出线程使用 `thread_data` 副本安全，但 `saved_list` 是共享列表，后台线程 `append()` 无同步保护 | `main.py:669, 786-793` | Medium | Open |
| 7 | `_on_close` 仍未等待 GIF 线程完成；用户关闭窗口时可能中断导出导致残缺文件 | `main.py:1075-1079` | Medium | Open |
| 8 | `_export_gif` 中 `progress_win.grab_set()` 如果导出线程异常，弹窗可能永远不关闭（`_on_done` 不执行） | `main.py:747, 797-805` | Medium | Open |
| 9 | DXF 导出手写原始 DXF 格式，缺少 `ezdxf` 依赖（requirements 有但 `dxf_export.py` 未使用）；LWPOLYLINE 顶点数超过 9999 时部分 CAD 软件不支持 | `ui/dxf_export.py` | Low | Open |
| 10 | `generate_random_params` 仍只生成 law 1-5，遗漏 law 6（七次多项式） | `ui/params.py:121-122` | Medium | Open |
| 11 | `ParameterModel` docstring 写 `tc_law, hc_law : int — 推程/回程运动规律编号 (1-5)`，遗漏 6 | `ui/params.py:57` | Low | Open |

### 1.3 Computation Engine

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 12 | `compute_rise`/`compute_return` ValueError 消息全为英文（如 `"law must be 1-6"`），不经过 i18n，中文用户看到英文异常 | `cam_mechanics.py:33-39, 108-115` | Medium | Open |
| 13 | `compute_rise` 允许 `h=0` 但 `compute_full_motion` 拒绝 `h<=0`，API 不一致 | `cam_mechanics.py:35 vs 198` | Low | Open |
| 14 | 当 `e ≈ r_0` 时，`s_0` 极小，`compute_pressure_angle` 中 `s_0 + s` 接近零，压力角跳至 ±90°，无警告 | `cam_mechanics.py:296, 336` | Medium | Open |
| 15 | `compute_curvature_radius` 对于凸轮尖点（曲率半径→0）返回极小负值/`inf`，无下界保护；下游 `r_r >= min_abs_rho` 判断可能产生误报 | `cam_mechanics.py` | Medium | Open |

### 1.4 Internationalization

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 16 | GIF 进度标签 `"0 / 360"` 和帧号显示为硬编码，未经过 i18n | `main.py:765-768, 777` | Low | Open |
| 17 | 信息面板背景色硬编码 `(1.0, 1.0, 1.0, 0.8)` 白色，暗色模式下不可读 | `main.py:916` | Medium | Open |
| 18 | ROADMAP 中文/英文版本不同步：英文版缺失 Phase 16+ 内容 | `ROADMAP.en.md` | Low | Open |

### 1.5 Performance

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 19 | GIF 导出已改为帧流式写入，但每帧仍需创建独立 `Figure` → `savefig` → 关闭，360 帧约 12-20 秒；可用 `FigureCanvasAgg` 直接渲染避免文件 I/O | `ui/animation.py` | Medium | Open |
| 20 | 动画帧更新使用 `canvas.draw_idle()` 带 `ANIM_FRAME_SKIP` 跳帧，但 `draw_idle` 仍重绘整个 Figure；可用 `blit` 局部刷新仅动画区域 | `main.py:1004-1005` | Medium | Open |
| 21 | `_on_start` 每次重新计算 `delta_full = np.linspace(0, 2π, 360)` 和基圆/偏距圆，但 `n_points` 可能不是 360，硬编码 360 导致基圆/偏距圆与凸轮廓形状点数不匹配 | `main.py:468-472` | Medium | Open |

### 1.6 Testing & Engineering

| # | Issue | Location | Severity | Status |
|---|------|------|:--------:|--------|
| 22 | UI 组件（`ctk_sidebar`, `ctk_toolbar`, `ctk_components`）零测试覆盖 | `tests/` | High | Open |
| 23 | `ConfigManager` 涉及文件 I/O (`~/.camforge/config.json`)，无任何测试（损坏文件/权限错误/缺失目录） | `tests/` | Medium | Open |
| 24 | `dxf_export.py` 无测试（顶点数、闭合标志、图层名验证） | `tests/` | Medium | Open |
| 25 | 测试硬编码依赖 `N_POINTS=360`（如 `alpha[45]`、`x[270:]`），若默认分辨率变更则全部失败 | `tests/test_cam_mechanics.py` | Medium | Open |
| 26 | `TestI18n` 在 `test_cam_mechanics.py` 和 `test_i18n.py` 中重复 | `tests/` | Low | Open |
| 27 | CI 仅运行 `ruff lint` + `pytest`，缺少 mypy/pyright 类型检查步骤 | `.github/workflows/ci.yml` | Low | Open |

### 1.7 Feature Gaps

| # | Feature | Description | Priority |
|---|---------|-------------|:--------:|
| 28 | 平底从动件 | 目前仅支持尖底(r_r=0)和滚子从动件，缺少平底从动件类型 | High |
| 29 | 逆向设计 | 给定输出要求反推凸轮参数（ROADMAP Phase 16.1 #4），当前只能正向计算 | High |
| 30 | 运动曲线对比 | 支持加载参考曲线叠加显示（ROADMAP Sprint 2 S2-2），当前无法对比 | Medium |
| 31 | 摆动从动件 | 仅支持直动从动件，不支持摆动从动件凸轮机构 | Medium |
| 32 | 凸轮廓形公差标注 | DXF/SVG 导出缺少公差、粗糙度等制造标注 | Low |
| 33 | 批量参数分析 | 无法对参数范围进行扫描，生成参数敏感度图 | Low |

---

## II. v0.7.0 Development Plan

> **Target Version**: v0.7.0
> **Theme**: Architecture Restructuring + Core Feature Expansion + Quality Hardening
> **Principle**: Each Sprint delivers independently verifiable results; each task has clear acceptance criteria.

---

### Sprint 1 — Architecture Decoupling & Type Safety (v0.7.0-alpha.1)

**Goal**: Split `CamSimulator` God Class, introduce typed data model for simulation results, make core pipeline independently testable.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S1-1 | Extract `SimulationResult` dataclass from `sim_data` dict — encapsulate all 22+ keys with typed fields | New `ui/sim_result.py`, modify `main.py`, `ui/animation.py`, `ui/export.py`, `ui/plots.py` | (1) `SimulationResult` is a `@dataclass` with all fields typed; (2) `main.py:_on_start` returns `SimulationResult`; (3) All consumers use attribute access instead of dict key; (4) All existing tests pass; (5) `mypy --strict` passes on new file |
| S1-2 | Extract `SimulationPipeline` class from `_on_start` — encapsulate parameter validation → computation → result assembly as a stateless callable | New `ui/pipeline.py`, modify `main.py` | (1) `_on_start` reduced to ≤30 lines (call pipeline + update UI); (2) `SimulationPipeline.run(model) -> SimulationResult` can be unit-tested without GUI; (3) Add `test_pipeline.py` with ≥5 tests covering valid, invalid, edge cases; (4) All existing tests pass |
| S1-3 | Extract `AnimationController` from `CamSimulator` — encapsulate `_start_animation`, `_stop_animation`, `_animate_frame`, `_draw_single_frame`, frame navigation | New `ui/anim_controller.py`, modify `main.py` | (1) `CamSimulator` no longer has `animating`, `paused`, `current_frame`, `anim_id` attributes; (2) These are managed by `AnimationController`; (3) Animation functionality unchanged; (4) `CamSimulator.__init__` body ≤50 lines |
| S1-4 | Extract callback list into reusable constant — eliminate 3×11 callback repetition | `main.py`, optionally new `ui/callbacks.py` | (1) Callback list defined once, shared by `_build_gui`, `_on_language_change`, `_on_theme_change`; (2) Adding a new callback requires editing only one place |
| S1-5 | Fix `generate_random_params` — add law 6 support, update `ParameterModel` docstring | `ui/params.py` | (1) `tc_law = random.randint(1, 6)`; (2) `hc_law = random.randint(1, 6)`; (3) docstring says `(1-6)`; (4) Test in `test_ui.py` updated to accept law 6 |

**Verification**: Run `pytest` — all pass. `ruff check .` — clean. Manual test: start simulation, pause, resume, random params — all work.

---

### Sprint 2 — Computation Engine Hardening (v0.7.0-alpha.2)

**Goal**: Fix computation edge cases, complete i18n for engine errors, improve numerical robustness.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S2-1 | Add `e ≈ r_0` warning in `compute_pressure_angle` — when `s_0 < epsilon` (e.g., `s_0 < r_0 * 0.05`), return a warning flag alongside the computed values | `cam_mechanics.py` | (1) `compute_pressure_angle` returns `(alpha_deg, warning)` or raises `ValueError` when `s_0` is unreasonably small; (2) UI shows warning in status bar; (3) Add test for `e = r_0 - 0.01` case |
| S2-2 | Unify `h=0` handling — `compute_rise`/`compute_return` should accept `h=0` (returns zero array), and `compute_full_motion` should also accept it (degenerate cam, valid for analysis) | `cam_mechanics.py` | (1) `compute_full_motion(h=0, ...)` returns valid arrays of zeros; (2) `compute_rise(h=0, ...)` returns zeros; (3) Add tests for `h=0` full motion; (4) UI handles `h=0` gracefully |
| S2-3 | Complete engine error i18n — all `ValueError` messages in `cam_mechanics.py` use i18n keys; add corresponding zh/en translations to `i18n.py` | `cam_mechanics.py`, `i18n.py` | (1) No raw English error strings in `cam_mechanics.py`; (2) All errors have i18n keys like `error.param.delta_positive`, `error.param.law_range`; (3) Add tests verifying error messages are localized |
| S2-4 | Fix base/offset circle hardcoding — use `n_points` from `sim_data` for `delta_full`, `x_base`, `y_base`, `x_offset`, `y_offset` | `main.py:468-472`, `ui/pipeline.py` (after S1-2) | (1) `delta_full = np.linspace(0, 2π, n_points, endpoint=False)`; (2) Base/offset circles match profile point count; (3) Verify with `n_points=720` that all arrays are same length |
| S2-5 | Add curvature radius lower bound protection — clamp extreme outliers (e.g., `|rho| > 1e6`) to `inf` for cleaner downstream analysis | `cam_mechanics.py` | (1) `compute_curvature_radius` clips `|rho| > threshold` to `±inf`; (2) Clipping threshold configurable (default 1e6); (3) Add test; (4) Min curvature warning more reliable |

**Verification**: Run `pytest` — all pass including new tests. Manual test: try `e = r_0`, `h = 0`, `n_points = 720` — proper warnings shown, no crashes.

---

### Sprint 3 — UI Robustness & Info Panel Improvements (v0.7.0-beta.1)

**Goal**: Fix thread safety, dark mode issues, info panel, and i18n gaps.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S3-1 | Fix GIF export `saved_list` thread safety — use `threading.Lock` or `queue.Queue` for sharing between main thread and GIF thread | `main.py` | (1) `saved_list.append()` in background thread is protected by lock; (2) No race condition on rapid export; (3) Manual test: export GIF twice rapidly — no crash |
| S3-2 | Fix `_on_close` to wait for GIF thread — set a `_gif_thread` reference, join with timeout on close | `main.py` | (1) On close, if GIF thread is running, wait up to 5 seconds then destroy; (2) No orphaned threads; (3) No partial files left |
| S3-3 | Fix GIF progress dialog stuck on exception — add `finally` block with `progress_win.destroy()` guarantee; add timeout fallback | `main.py:796-805` | (1) Even if `generate_gif_frames` raises, progress dialog closes; (2) Error shown in status bar; (3) Add manual test: induce GIF export error → dialog closes |
| S3-4 | Fix info panel dark mode — info panel background adapts to theme (`rgba` based on `_dark_mode`) | `main.py:916`, `ui/animation.py` | (1) Light mode: white semi-transparent background; (2) Dark mode: dark semi-transparent background; (3) Text color adapts; (4) Manual test: toggle theme — info panel readable in both |
| S3-5 | i18n progress label — replace hardcoded `"0 / 360"` and `f"{i+1} / {t}"` with i18n template | `main.py:765-768, 777` | (1) Add i18n key `export.gif_dialog.progress` with `{current}/{total}` format; (2) Chinese: `0 / 360` (unchanged), English: `0 / 360` (unchanged, but template-driven) |
| S3-6 | Fix DXF export — migrate from hand-written DXF to `ezdxf` library (already in requirements.txt as `ezdxf>=1.0,<2` but unused) | `ui/dxf_export.py` | (1) Use `ezdxf` for DXF generation; (2) Proper LWPOLYLINE with no 9999-vertex limit; (3) Support `CAM_THEORY` and `CAM_ACTUAL` layers; (4) Add `test_dxf_export.py` with ≥3 tests; (5) Files open correctly in AutoCAD/LibreCAD |

**Verification**: `pytest` all pass. Manual test: dark mode info panel readable; GIF export + close window; DXF opens in CAD viewer.

---

### Sprint 4 — Flat-Faced Follower Support (v0.7.0-beta.2)

**Goal**: Add flat-faced (平底) follower type as first new engineering feature.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S4-1 | Add follower type enum/parameter to `ParameterModel` — `follower_type: str` with values `'knife'`, `'roller'`, `'flat'` | `ui/params.py`, `cam_mechanics.py` | (1) `ParameterModel` includes `follower_type` field; (2) Default `'knife'` for backward compatibility; (3) Preset JSON includes follower type |
| S4-2 | Implement flat-faced follower computation in `cam_mechanics.py` — actual profile = envelope of follower face positions; cam width calculation (`b >= 2*ρ_min`) | `cam_mechanics.py` | (1) New function `compute_flat follower_profile(x, y, ...)`; (2) Returns actual profile coordinates and min cam width; (3) Add ≥5 unit tests with analytical verification for simple case (circular cam) |
| S4-3 | Add flat-faced follower visualization — draw flat face rectangle instead of roller circle in animation | `ui/animation.py`, `main.py` | (1) When `follower_type='flat'`, animation shows flat face; (2) No roller circle drawn; (3) Info panel shows cam width; (4) Manual test: flat follower animates correctly |
| S4-4 | Add sidebar follower type selector — combo box or radio buttons switching between knife/roller/flat | `ui/ctk_sidebar.py` | (1) New combo row for follower type; (2) Roller radius input is disabled when type is not 'roller'; (3) i18n keys for follower type names |
| S4-5 | Export flat-faced follower data — CSV/Excel include cam width column; DXF exports actual profile; SVG/PNG show flat face | `ui/export.py`, `ui/dxf_export.py` | (1) CSV/Excel have `cam_width` column for flat follower; (2) DXF includes actual profile; (3) Static plots show cam width annotation |

**Verification**: `pytest` all pass. Manual test: select flat follower → compute → animation shows flat face → export DXF → open in CAD → verify profile. Compare analytical solution for circular cam.

---

### Sprint 5 — Test Coverage & CI Hardening (v0.7.0-rc.1)

**Goal**: Bring test coverage to critical modules, add CI type checking, clean up test structure.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S5-1 | Add `test_pipeline.py` — test `SimulationPipeline.run()` with valid/invalid/edge models (leveraging S1-2) | `tests/test_pipeline.py` | (1) ≥8 tests: valid params, invalid angles sum, zero stroke, extreme offset, law 6, high n_points; (2) All pass; (3) Pipeline is importable without GUI |
| S5-2 | Add `test_config.py` — test `ConfigManager` with temp directory, corrupt file, missing file, permission error | `tests/test_config.py` | (1) ≥6 tests: load/save round-trip, corrupt JSON, missing file, invalid paths; (2) Uses `tmp_path` fixture; (3) No side effects on real `~/.camforge/` |
| S5-3 | Add `test_dxf_export.py` — verify DXF content structure (header, entities, layer names, closure flag) | `tests/test_dxf_export.py` | (1) ≥4 tests: single profile, dual profile, empty profile, layer name verification; (2) Can be parsed by `ezdxf`; (3) Vertex count matches input |
| S5-4 | Remove `TestI18n` duplication from `test_cam_mechanics.py` — keep only in `test_i18n.py`, add any missing test cases | `tests/test_cam_mechanics.py`, `tests/test_i18n.py` | (1) No i18n tests in `test_cam_mechanics.py`; (2) `test_i18n.py` covers all previously tested scenarios; (3) All tests pass |
| S5-5 | Fix N_POINTS-dependent test fragility — compute expected indices from `n_points` parameter instead of hardcoding | `tests/test_cam_mechanics.py` | (1) No hardcoded index values like `alpha[45]` or `x[270:]`; (2) Use `int(angle * n_points / 360)` pattern; (3) Tests pass with `n_points=360`, `n_points=720`, `n_points=180` |
| S5-6 | Add pyright/mypy step to CI — type check on Python 3.12 | `.github/workflows/ci.yml` | (1) CI runs `pyright` or `mypy` after lint; (2) Existing code passes with `basic` mode; (3) New `SimulationResult` dataclass passes `strict` mode |
| S5-7 | Add `test_ui_params.py` — comprehensive `ParameterModel` tests including `from_dict`, `to_dict`, `validate`, `angles_sum_to_360`, random params with law 6 | `tests/test_ui_params.py` | (1) ≥10 tests; (2) `generate_random_params()` returns law 1-6; (3) `from_dict` / `to_dict` round-trip; (4) `angles_sum_to_360` edge cases |

**Verification**: `pytest --cov` shows ≥90% coverage for `cam_mechanics.py`, `ui/params.py`, `ui/pipeline.py`, `ui/config.py`, `ui/dxf_export.py`. CI green on all 3 OS.

---

### Sprint 6 — Performance Optimization & UX Polish (v0.7.0)

**Goal**: Optimize animation rendering, improve GIF export speed, polish dark mode, prepare release.

| ID | Task | Files | Acceptance Criteria |
|----|------|-------|---------------------|
| S6-1 | Implement matplotlib blitting for animation — `canvas.copy_from_bbox` + `restore_region` + selective artist redraw | `main.py`, `ui/anim_controller.py` | (1) `_animate_frame` uses blit instead of `draw_idle`; (2) Measurable FPS improvement: ≥30% faster rendering; (3) No visual artifacts; (4) Fallback to `draw_idle` if blit fails |
| S6-2 | Optimize GIF export — use `FigureCanvasAgg` direct rendering instead of `savefig`; skip `Figure` recreation per frame | `ui/animation.py` | (1) Per-frame overhead reduced by ≥40% (measure with `time.perf_counter`); (2) Total GIF export <10 seconds for 360 frames; (3) Output quality unchanged; (4) Add benchmark test |
| S6-3 | Dark mode polish — ensure all plot elements (grid, spines, tick labels, legend, title) adapt to dark mode | `main.py`, `ui/plots.py`, `ui/animation.py` | (1) No white-on-white or black-on-black text in dark mode; (2) Grid lines subtle but visible; (3) Legend background matches theme |
| S6-4 | Add motion law name annotations on motion curves — show law name at midpoint of rise/return phases | `ui/plots.py` | (1) Rise phase midpoint shows `t("law.N", lang)` in appropriate color; (2) Return phase same; (3) No overlap with data; (4) Toggle-able via sidebar switch |
| S6-5 | Update documentation — README, ROADMAP.en.md, CHANGELOG, help dialog for v0.7.0 | `README.md`, `README.en.md`, `ROADMAP.en.md`, `CHANGELOG.md`, `ui/ctk_toolbar.py` | (1) README mentions flat follower; (2) ROADMAP.en.md syncs with Chinese version; (3) CHANGELOG has v0.7.0 entry; (4) Help dialog lists new features and shortcuts |
| S6-6 | Version bump & release — update `pyproject.toml`, `cam_mechanics.__version__`, build & test executable | `pyproject.toml`, `cam_mechanics.py`, `build.bat` | (1) Version is `0.7.0`; (2) `pip install -e .` works; (3) `camforge` console command launches; (4) PyInstaller build succeeds on Windows |

**Verification**: Full regression test. GIF export benchmark <10s. Dark mode fully readable. Flat follower works end-to-end. Version 0.7.0 binary builds and runs.

---

## III. Sprint Dependency Graph

```
Sprint 1 (Architecture) ──── Sprint 2 (Engine) ──── Sprint 3 (UI Robustness)
      │                                                   │
      └────────────────── Sprint 4 (Flat Follower) ◄──────┘
                                    │
                            Sprint 5 (Tests & CI)
                                    │
                            Sprint 6 (Perf & Polish)
```

- **Sprint 1 → Sprint 2**: Pipeline extraction (S1-2) enables S2-4 fix
- **Sprint 1 → Sprint 4**: `SimulationResult` (S1-1) needed for flat follower data flow
- **Sprint 3 → Sprint 4**: Dark mode fix (S3-4) needed before flat follower visualization (S4-3)
- **Sprint 4 → Sprint 5**: Flat follower tests are part of S5
- **Sprint 5 → Sprint 6**: Test infrastructure needed before performance refactoring

---

## IV. Risk Assessment

| Risk | Mitigation |
|------|------------|
| God Class 拆分引起回归 | 每步拆分后运行全量 pytest + 手动验证核心流程 |
| matplotlib blitting 与 CustomTkinter 不兼容 | 预留 fallback 到 `draw_idle`；先在独立脚本验证 blit |
| 平底从动件数学复杂度 | 先实现最简情况（对心平底），再扩展偏置；有解析解验证 |
| `ezdxf` 迁移导致 DXF 格式变化 | 增加对比测试：旧输出 vs 新输出在 LibreCAD 中打开一致 |
| 性能优化影响输出质量 | GIF 逐帧像素对比（允许 <1% 像素差异） |

---

## V. Version Milestones

| Milestone | Version | Sprint | Key Deliverables |
|-----------|---------|--------|-----------------|
| Alpha 1 | v0.7.0a1 | Sprint 1 | `SimulationResult` + `SimulationPipeline` + `AnimationController` + callback refactor |
| Alpha 2 | v0.7.0a2 | Sprint 2 | Engine i18n, `e≈r_0` warning, `h=0` support, curvature clamp, n_points fix |
| Beta 1 | v0.7.0b1 | Sprint 3 | Thread safety, dark mode info panel, `ezdxf` migration, progress i18n |
| Beta 2 | v0.7.0b2 | Sprint 4 | Flat-faced follower computation, visualization, export |
| RC | v0.7.0rc1 | Sprint 5 | Full test coverage, CI hardening, test cleanup |
| Release | v0.7.0 | Sprint 6 | Blitting animation, fast GIF export, dark mode polish, docs, release |

---

## VI. Issue Status Summary

```
Resolved in prior phases:
  #11 (index bounds)     → P3-1 ✅
  #12 (angle sum)        → P3-2 ✅
  #13 (frame index)      → P3-3 ✅
  #23 (i18n tests)       → test_i18n.py ✅
  #24-27 (test gaps)     → Phase 3 tests ✅
  #16 (N_POINTS hardcode) → P6-6/Phase 13 ✅
  #19 (规律 suffix)      → Fixed ✅
  #18 (error.unknown_law) → P3-6 ✅

Targeted in v0.7.0:
  #1  (God Class)          → S1-1, S1-2, S1-3
  #2  (_on_start length)   → S1-2
  #3  (sim_data dict)      → S1-1
  #4  (callback repetition) → S1-4
  #5  (private method)     → S1-2
  #6  (saved_list race)    → S3-1
  #7  (on_close thread)    → S3-2
  #8  (progress stuck)     → S3-3
  #9  (DXF raw format)     → S3-6
  #10 (random law 6)       → S1-5
  #11 (docstring 1-5)      → S1-5
  #12 (engine i18n)        → S2-3
  #13 (h=0 inconsistency)  → S2-2
  #14 (e≈r_0 warning)      → S2-1
  #15 (curvature outliers) → S2-5
  #16 (progress i18n)      → S3-5
  #17 (info panel dark)    → S3-4
  #19 (GIF perf)           → S6-2
  #20 (blit animation)     → S6-1
  #21 (n_points 360)       → S2-4
  #22-27 (test gaps)       → S5-1 through S5-7
  #28 (flat follower)      → S4-1 through S4-5

Deferred beyond v0.7.0:
  #18 (ROADMAP EN sync)   → Post-release doc task
  #29 (inverse design)    → v0.8.0
  #30 (curve comparison)   → v0.8.0
  #31 (oscillating follower) → v1.0.0
  #32 (tolerance annotation) → v1.0.0
  #33 (batch param sweep)  → v1.0.0
```

---

## VII. Priority Principles

1. **Correctness First** — Issues affecting results (e≈r₀ warning, h=0 inconsistency, curvature outliers) before UX
2. **Architecture Before Feature** — Split God Class first (Sprint 1), then add flat follower (Sprint 4) on clean architecture
3. **Testability First** — Every extracted module must be unit-testable without GUI (Sprint 1 enables Sprint 5)
4. **Performance Incrementally** — Blitting and GIF optimization only after correctness is locked (Sprint 6)
5. **Incremental & Verifiable** — Each Sprint produces a runnable alpha/beta/rc with all tests passing
