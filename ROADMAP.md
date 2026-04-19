中文 | [English](ROADMAP.en.md)

# CamForge Roadmap

> 项目现状分析与后续优化方向

---

## 一、现存问题

### 1.1 代码架构

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 1 | `CamSimulator` 类超过 **1350 行**，GUI 构建、计算、动画、导出、i18n 逻辑全部耦合 | `main.py` | 高 |
| 2 | `_build_gui` 方法约 **270 行**，侧边栏/工具栏/图表布局全部内联，label+entry 模式重复 8 次未提取 | `main.py:261-565` | 中 |
| 3 | 计算状态（`sim_data`）与 GUI 状态（widget 引用、动画标志）混存于同一类，无独立数据模型 | `main.py:149-180` | 中 |

### 1.2 健壮性

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 4 | GIF 导出线程读取 `sim_data` 无锁保护，`saved_list.append()` 与主线程并发无同步 | `main.py:1273-1438` | 高 |
| 5 | `_on_start` 中 `compute_full_motion`/`compute_cam_profile` 无 try/except 包裹，异常时应用崩溃 | `main.py:672-735` | 中 |
| 6 | `_read_params` 静默截断浮点角度（`int(float(...))`），用户输入 90.9 变为 90 无提示 | `main.py:629-639` | 中 |
| 7 | `validate_params` 允许 `e < 0`（检查 `abs(e)`），但 `compute_cam_profile` 拒绝 `e < 0`，不一致 | `cam_mechanics.py:541 vs 289` | 中 |
| 8 | `_export_excel` 的 `wb.save()` 无 try/except，磁盘满或路径无效时崩溃 | `main.py` | 中 |
| 9 | `_on_download` 中各 `fig.savefig()` 无错误处理 | `main.py` | 中 |
| 10 | `_on_close` 不等待 GIF 导出线程完成，可能中断导出 | `main.py` | 低 |

### 1.3 计算引擎

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 11 | `compute_full_motion` 中 `i1/i2/i3` 由 `int(round(...))` 计算，四角之和为 360 时 i3 可能不等于 360，导致索引越界 | `cam_mechanics.py:226-228` | 高 |
| 12 | `compute_full_motion` 不验证四角之和为 360°，仅 `validate_params` 检查，直接调用可产生错误结果 | `cam_mechanics.py:168-262` | 中 |
| 13 | `compute_anim_frame_data` 不验证帧索引 `i` 的范围（`0 <= i < len(s)`），越界时 IndexError 无描述 | `cam_mechanics.py:369-450` | 中 |
| 14 | `e ≈ r_0` 时 `s_0` 极小，`compute_pressure_angle` 中 `s_0 + s` 接近零，压力角跳至 ±90° 无警告 | `cam_mechanics.py:296,336` | 中 |
| 15 | `compute_rise` 允许 `h=0` 但 `compute_full_motion` 拒绝 `h<=0`，API 不一致 | `cam_mechanics.py:35 vs 198` | 低 |
| 16 | `N_POINTS = 360` 硬编码，无法调整分辨率 | `cam_mechanics.py:8` | 低 |

### 1.4 国际化

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 17 | `compute_rise`/`compute_return` 的 `ValueError` 消息为纯英文，未走 i18n，异常传播到 UI 时中文用户看到英文 | `cam_mechanics.py:33-39,108-115` | 中 |
| 18 | `error.unknown_law` 在 `cam_mechanics.py` 中使用管道格式 `error.unknown_law|{law}`，与 i18n 键 `error.unknown_law` 不匹配，翻译永远无法命中 | `cam_mechanics.py:83,159` | 中 |
| 19 | 运动规律下拉列表中文"规律"后缀不一致（1/2 无，3/4/5 有） | `i18n.py:law.combo.*` | 低 |
| 20 | Logo 文本 "CamForge"、GIF 进度标签 "0 / 360" 等硬编码字符串未走 i18n | `main.py:294,1315` | 低 |

### 1.5 性能

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 21 | GIF 导出逐帧 `ax.clear()` + 全量重绘 360 次，极慢（30-60 秒），应使用 blitting 或预渲染 | `main.py:1338-1405` | 高 |
| 22 | GIF 导出将 360 帧 PIL Image 全部保留在内存（360-720 MB），可能导致内存不足 | `main.py:1327-1410` | 中 |

### 1.6 测试与工程化

| # | 问题 | 位置 | 严重程度 |
|---|------|------|:--------:|
| 23 | 无 i18n 测试（键完整性、回退行为、格式化参数） | `tests/` | 中 |
| 24 | 无压力角推程/回程阶段测试 | `tests/` | 中 |
| 25 | 无 `sn=-1`/`pz=-1`（旋向/偏距方向）的廓形测试 | `tests/` | 中 |
| 26 | 无 `compute_full_motion` 非整角度测试（如 91+59+120+90），未覆盖索引舍入逻辑 | `tests/` | 中 |
| 27 | 无 `compute_anim_frame_data` 边界帧索引测试（帧 0、帧 N-1） | `tests/` | 中 |
| 28 | 无 `pyproject.toml`、无版本号、无 `conftest.py` | 项目根目录 | 中 |
| 29 | `requirements.txt` 无上界约束，numpy 2.x 可能破坏兼容性 | `requirements.txt` | 中 |
| 30 | 无类型注解，无法进行静态检查 | 全部文件 | 低 |

---

## 二、优化方向

### Phase 1 — 修复与加固（v0.2）✅ 已完成

- [x] **P1-1** 补全 `requirements.txt`，添加 `Pillow` 依赖
- [x] **P1-2** 修复跨平台字体：运行时检测系统可用中文字体，自动回退
- [x] **P1-3** 修复跨平台滚轮事件：区分 Windows / macOS / Linux 的 `delta` 值与事件类型
- [x] **P1-4** 修复窗口最大化兼容性：按平台选择 `state('zoomed')` 或 `attributes('-fullscreen')`
- [x] **P1-5** 修复浮点校验问题：`_read_params` 中角度先转 `int` 再传入 `validate_params`
- [x] **P1-6** 添加 `LICENSE` 文件（MIT）
- [x] **P1-7** 完善 `.gitignore`（IDE 目录、虚拟环境、构建产物等）
- [x] **P1-8** 为 `cam_mechanics.py` 添加单元测试（pytest，59 项全部通过）

### Phase 2 — 重构与性能（v0.3）✅ 已完成

- [x] **P2-2** 提取魔法数字为命名常量或配置项
- [x] **P2-3** GIF 导出改为后台线程 + 进度条，避免 UI 冻结
- [x] **P2-4** 消除动画与 GIF 导出间的推杆绘制重复代码，抽取为共享函数
- [x] **P2-5** 静态图导出改为直接重新计算绘图，消除 `BlendedGenericTransform` hack
- [x] **P2-6** 动画结束后支持「重播」按钮，无需重新计算
- [x] **P2-7** 下载文件名通过 i18n 键值动态生成，随语言切换
- [x] **P2-8** 提取颜色常量为主题字典，为深色模式做准备
- [x] **P2-9** 将方法内标准库 `import` 移至模块顶层
- [x] **P2-10** 消除 `_plot_static` 与 `_on_download` 间的静态绘图代码重复

### Phase 3 — 正确性修复（v0.4）✅ 已完成

目标：修复影响功能正确性的关键问题，补全测试覆盖。

- [x] **P3-1** 修复 `compute_full_motion` 索引舍入问题：添加 `i1/i2/i3` 边界检查，确保 `i3 <= N_POINTS`
- [x] **P3-2** `compute_full_motion` 添加四角之和验证（与 `validate_params` 一致）
- [x] **P3-3** `compute_anim_frame_data` 添加帧索引范围检查
- [x] **P3-4** `_on_start` 添加 try/except 包裹计算调用，异常时显示友好错误而非崩溃
- [x] **P3-5** 修复 `validate_params` 与计算引擎的验证不一致：`e` 不允许为负值
- [x] **P3-6** 修复 `error.unknown_law` 格式：`cam_mechanics.py` 中使用 i18n 键格式而非管道格式
- [x] **P3-7** `_read_params` 浮点截断时添加用户提示（如 "角度 90.9 已取整为 90"）
- [x] **P3-8** `_export_excel` 和 `_on_download` 添加 try/except 错误处理
- [x] **P3-9** GIF 导出线程安全：添加 `threading.Lock` 保护 `sim_data` 读取
- [x] **P3-10** 补全测试：i18n 键完整性、非整角度索引、边界帧索引、`sn=-1`/`pz=-1` 廓形、压力角推程/回程

### Phase 4 — 性能优化（v0.5）✅ 已完成

目标：提升 GIF 导出性能和内存效率。

- [x] **P4-1** GIF 导出改为逐帧渲染+即时写入流，避免 360 帧 PIL Image 全部驻留内存
- [x] **P4-2** GIF 导出使用 blitting 或预渲染优化，减少逐帧 `ax.clear()` + 全量重绘开销
- [x] **P4-3** Excel 导出改为批量写入（`ws.append` 行写入替代逐单元格）

### Phase 5 — 代码架构（v0.6）✅ 已完成

目标：拆分大类，改善可维护性。

- [x] **P5-1** 拆分 `CamSimulator` 为独立模块：
  ```
  ui/
  ├── __init__.py     # 包初始化
  ├── constants.py    # 渲染常量与主题颜色
  ├── drawing.py      # 共享绘图函数
  ├── params.py       # 参数数据模型与随机参数生成
  └── plots.py        # 静态图表绘制
  ```
- [x] **P5-2** 提取参数数据模型类（`ParameterModel`），分离计算状态与 GUI 状态
- [x] **P5-3** `_build_gui` 拆分为 `_build_sidebar`、`_build_toolbar`、`_build_figure` 等子方法

### Phase 6 — 功能增强（v0.7）✅ 已完成

目标：扩展仿真功能，提升工程实用性。

- [x] **P6-1** 滚子从动件支持：增加滚子半径参数，计算实际廓形（等距曲线）与理论廓形
- [x] **P6-2** 压力角曲线图：新增压力角随转角变化的独立图表
- [x] **P6-3** 凸轮轮廓曲率半径计算与显示，标注最小曲率半径位置
- [x] **P6-4** 参数预设系统：保存/加载常用凸轮配置（JSON 文件）
- [x] **P6-5** 压力角阈值可配置（侧边栏输入框）
- [x] **P6-6** `N_POINTS` 可配置化，支持更高或更低的离散分辨率

### Phase 7 — 体验升级（v0.8）✅ 已完成

目标：打磨交互细节，提升视觉与操作体验。

- [x] **P7-1** 深色模式支持（tkinter 主题 + matplotlib 样式切换）
- [x] **P7-2** 动画帧进度条：显示当前帧/总帧数，支持拖动跳转
- [x] **P7-3** 窗口缩放自适应：监听 `Configure` 事件动态调整 Figure 尺寸
- [x] **P7-4** 参数输入实时校验：输入时即时提示范围错误
- [x] **P7-5** 导出格式扩展：支持 SVG 矢量图、CSV 数据表导出
- [x] **P7-6** i18n 细节修复：运动规律后缀统一、Logo/进度标签国际化

### Phase 8 — 工程化与发布（v1.0）✅ 已完成

目标：达到可发布质量，支持便捷安装与分发。

- [x] **P8-1** 添加 `pyproject.toml`，支持 `pip install camforge`
- [x] **P8-2** 添加版本号（`__version__`），窗口标题显示版本
- [x] **P8-3** GitHub Actions CI：自动运行测试、代码风格检查（ruff）
- [x] **P8-4** 代码覆盖率目标：`cam_mechanics.py` ≥ 90%（实际 95%），整体 ≥ 70%（实际 95%）
- [x] **P8-5** 添加类型注解，配置 pyright 静态检查
- [x] **P8-6** `requirements.txt` 添加上界约束，防止 numpy 2.x 等破坏性升级
- [x] **P8-7** 变更日志（CHANGELOG.md）维护

### Phase 9 — v0.2 现代化 UI 与性能（v0.2）✅ 已完成

目标：现代化 UI 布局，提升性能和可维护性。

- [x] **P9-1** 新 2 行 4 列网格布局：第一行（位移 | 速度 | 加速度 | 廓形），第二行（压力角 | 曲率 | 动画 | 信息面板）
- [x] **P9-2** 模块化架构：提取 `I18nManager`、`ThemeManager`、`ExportManager`、`SidebarBuilder`、`AnimationController` 到 `ui/` 包
- [x] **P9-3** NumPy 向量化：`compute_roller_profile` 和 `compute_curvature_radius` 使用 `np.roll`，10 倍 + 性能提升
- [x] **P9-4** 主题切换控件缓存：遍历缓存控件列表替代递归树遍历，5 倍 + 性能提升
- [x] **P9-5** `ParameterModel` 类型安全数据模型：带校验和转换的类型安全参数传递
- [x] **P9-6** 动画渲染提取：`ui/animation.py` 中的 `render_frame_artists` 和 `update_info_panel` 纯函数
- [x] **P9-7** GIF 生成提取：带进度回调的 `generate_gif_frames` 独立函数
- [x] **P9-8** Windows 独立执行文件：PyInstaller 打包带图标，70 MB 单文件

### Phase 10 — v0.3 简化布局（v0.3）✅ 已完成

目标：简化布局，合并相关图表。

- [x] **P10-1** v0.3.0：三 Y 轴运动线图（位移/速度/加速度合并）
- [x] **P10-2** v0.3.1：双 Y 轴几何约束图（压力角/曲率半径合并）
- [x] **P10-3** 移除静态廓形图（廓形仍在动画中显示）
- [x] **P10-4** 简化布局为 2x2 网格：上方静态图，下方动态图

### Phase 11 — v0.3.2 左右分区布局 ✅ 已完成

目标：优化动画显示区域。

- [x] **P11-1** 左右分区：左侧静态图（运动线图+几何约束），右侧动态图（动画+信息面板）
- [x] **P11-2** 动画区域扩大，信息面板移至右侧边缘
- [x] **P11-3** GridSpec 2x3，宽度比例 [1, 1.6, 0.4]

### Phase 12 — v0.4.0 布局优化与i18n完善 ✅ 已完成

目标：优化布局间距，完善国际化支持。

- [x] **P12-1** 三列布局：静态图 | 空白间隔 | 动态图，宽度比例 [1, 0.25, 0.9]
- [x] **P12-2** 增大运动线图右侧第二 Y 轴偏移量（45→60 像素）
- [x] **P12-3** 状态栏改为两行布局：第一行状态消息，第二行行程/初始位移/最大压力角
- [x] **P12-4** 按钮顺序调整：加载预设 → 保存预设 → 下载
- [x] **P12-5** CSV/SVG/预设文件名国际化（中文模式下使用中文文件名）
- [x] **P12-6** 状态栏标签使用纯文本（避免 LaTeX 符号显示问题）

### Phase 13 — v0.4.1 Bug 修复与优化 ✅ 已完成

目标：修复 n_points 相关 bug，优化显示效果。

- [x] **P13-1** 修复 `compute_full_motion` 索引缩放：`i = angle_deg * (n_points / 360)`
- [x] **P13-2** 修复动画帧角度缩放：凸轮旋转角度、法线/切线计算
- [x] **P13-3** `n_points` 改为函数参数传递，不再修改全局变量
- [x] **P13-4** GIF 导出修复：横纵轴等比例、滚子数据传递
- [x] **P13-5** 曲率半径干涉警告使用绝对值比较
- [x] **P13-6** 滚子可视化线宽与凸轮廓形一致（linewidth=2）
- [x] **P13-7** 下载选项"廓形"改为"廓形图"
- [x] **P13-8** 速度滑块标签与滑块水平对齐
- [x] **P13-9** 低离散点数时样条插值平滑显示（n_points < 180）

### Phase 14 — v0.4.2 代码清理 ✅ 已完成

目标：清理冗余文件和代码，提升代码质量。

- [x] **P14-1** 删除重复图标文件 `CamForge.ico`（保留 `camforge.ico`）
- [x] **P14-2** 删除自动生成的 `CamForge-v0.4.1.spec`
- [x] **P14-3** 移除 `main.py` 未使用的导入：`BytesIO`, `compute_rotated_cam`, `compute_anim_frame_data`, `compute_pressure_angle_arc`
- [x] **P14-4** 移除 `cam_mechanics.py` 未使用的变量：`delta_01`, `delta_02`
- [x] **P14-5** 修复 `i18n.py` 行过长问题（拆分长字符串）
- [x] **P14-6** 重组 `main.py` 导入语句（排序、分组）
- [x] **P14-7** 更新 `.gitignore` 忽略自动生成的 spec 文件

### Phase 15 — v0.4.3 七次多项式运动规律 ✅ 已完成

目标：添加七次多项式运动规律（4-5-6-7 多项式）。

- [x] **P15-1** 在 `compute_rise()` 中添加 law=6 七次多项式计算
- [x] **P15-2** 在 `compute_return()` 中添加 law=6 七次多项式计算
- [x] **P15-3** 更新运动规律验证从 (1,2,3,4,5) 到 (1,2,3,4,5,6)
- [x] **P15-4** 更新错误消息从 "law must be 1-5" 到 "law must be 1-6"
- [x] **P15-5** 添加 i18n 翻译：`law.6`、`law.combo.6`
- [x] **P15-6** 更新 `get_motion_law_list()` 返回 6 个选项
- [x] **P15-7** 添加 law=6 单元测试：边界条件、平滑性对比
- [x] **P15-8** 更新 README.md 和 README.en.md 运动规律表格
- [x] **P15-9** 更新 CHANGELOG.md 添加 v0.4.3 条目

---

## 三、问题统计

```
严重程度分布：
  高  ██████░░░░  3 项  （线程安全、索引越界、GIF 性能）
  中  ██████████████████  18 项  （验证不一致、错误处理、测试缺口、内存等）
  低  ████████░░░░░░  8 项  （i18n 细节、硬编码、类型注解等）
```

---

## 四、优先级原则

1. **正确性优先** — 影响功能结果的问题（索引越界、线程安全、验证不一致）优先于体验问题
2. **可测试性优先** — 为纯计算模块添加测试是后续所有重构的安全网
3. **性能其次** — GIF 导出 30-60 秒和 720 MB 内存是用户可感知的严重问题
4. **渐进重构** — 拆分大类时保持功能不变，每步可独立验证
5. **国际化一致性** — 所有用户可见字符串必须走 i18n，包括错误提示和格式细节
