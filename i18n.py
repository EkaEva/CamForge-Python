"""
CamForge 国际化模块
支持中文(zh)、英文(en)双语切换
"""

import platform

SUPPORTED_LANGS = ["zh", "en"]
DEFAULT_LANG = "zh"

LANG_DISPLAY_NAMES = {"zh": "中文", "en": "English"}

FONT_MAP = {
    "zh": {
        "tk": "Microsoft YaHei",
        "mpl": ["SimHei", "Microsoft YaHei", "FangSong"],
    },
    "en": {
        "tk": "Segoe UI",
        "mpl": ["DejaVu Sans"],
    },
}

# ---------------------------------------------------------------------------
# 翻译字典：flat key → {lang: text}
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    # ---- App ----
    "app.title": {
        "zh": "CamForge - 凸轮仿真",
        "en": "CamForge - Cam Simulator",
    },

    # ---- Sidebar Groups ----
    "sidebar.group.language": {
        "zh": "语言", "en": "Language",
    },
    "sidebar.group.motion": {
        "zh": "运动参数", "en": "Motion Parameters",
    },
    "sidebar.group.geometry": {
        "zh": "几何参数", "en": "Geometry Parameters",
    },
    "sidebar.group.law": {
        "zh": "运动规律", "en": "Motion Laws",
    },
    "sidebar.group.display": {
        "zh": "动态显示", "en": "Display Options",
    },
    "sidebar.group.theme": {
        "zh": "主题", "en": "Theme",
    },

    # ---- Sidebar Labels ----
    "sidebar.label.delta_0": {
        "zh": "推程运动角 (°)", "en": "Rise Angle (°)",
    },
    "sidebar.label.delta_01": {
        "zh": "远休止角 (°)", "en": "Outer Dwell Angle (°)",
    },
    "sidebar.label.delta_ret": {
        "zh": "回程运动角 (°)", "en": "Return Angle (°)",
    },
    "sidebar.label.delta_02": {
        "zh": "近休止角 (°)", "en": "Inner Dwell Angle (°)",
    },
    "sidebar.label.h": {
        "zh": "推杆最大位移 (mm)", "en": "Max Displacement (mm)",
    },
    "sidebar.label.omega": {
        "zh": "凸轮角速度 (rad/s)", "en": "Angular Velocity (rad/s)",
    },
    "sidebar.label.r_0": {
        "zh": "基圆半径 (mm)", "en": "Base Circle Radius (mm)",
    },
    "sidebar.label.e": {
        "zh": "偏距 (mm)", "en": "Offset (mm)",
    },
    "sidebar.label.tc_law": {
        "zh": "推程规律", "en": "Rise Law",
    },
    "sidebar.label.hc_law": {
        "zh": "回程规律", "en": "Return Law",
    },
    "sidebar.label.rotation": {
        "zh": "旋向", "en": "Rotation",
    },
    "sidebar.label.offset_dir": {
        "zh": "偏距方向", "en": "Offset Direction",
    },
    "sidebar.label.r_r": {
        "zh": "滚子半径 (mm)", "en": "Roller Radius (mm)",
    },
    "sidebar.label.n_points": {
        "zh": "离散点数", "en": "Discrete Points",
    },
    "sidebar.label.alpha_threshold": {
        "zh": "压力角阈值 (°)", "en": "Pressure Angle Threshold (°)",
    },

    # ---- Sidebar Checkbuttons ----
    "sidebar.cb.tangent": {
        "zh": "切线", "en": "Tangent",
    },
    "sidebar.cb.normal": {
        "zh": "法线", "en": "Normal",
    },
    "sidebar.cb.arc": {
        "zh": "压力角弧线", "en": "Pressure Angle Arc",
    },
    "sidebar.cb.boundaries": {
        "zh": "角度分界线", "en": "Phase Boundaries",
    },
    "sidebar.cb.base_circle": {
        "zh": "基圆", "en": "Base Circle",
    },
    "sidebar.cb.offset_circle": {
        "zh": "偏距圆", "en": "Offset Circle",
    },
    "sidebar.cb.limits": {
        "zh": "推杆上下限", "en": "Follower Limits",
    },
    "sidebar.cb.grid": {
        "zh": "网格线", "en": "Grid Lines",
    },

    # ---- Toolbar Buttons ----
    "toolbar.btn.start": {
        "zh": "开始仿真", "en": "Start",
    },
    "toolbar.btn.pause": {
        "zh": "暂停", "en": "Pause",
    },
    "toolbar.btn.resume": {
        "zh": "继续", "en": "Resume",
    },
    "toolbar.btn.replay": {
        "zh": "重播", "en": "Replay",
    },
    "toolbar.btn.clear_params": {
        "zh": "清除参数", "en": "Clear Params",
    },
    "toolbar.btn.clear_plots": {
        "zh": "清除图像", "en": "Clear Plots",
    },
    "toolbar.btn.random": {
        "zh": "随机凸轮", "en": "Random Cam",
    },
    "toolbar.btn.download": {
        "zh": "下载", "en": "Download",
    },
    "toolbar.btn.save_preset": {
        "zh": "保存预设", "en": "Save Preset",
    },
    "toolbar.btn.load_preset": {
        "zh": "加载预设", "en": "Load Preset",
    },
    "toolbar.label.speed": {
        "zh": "仿真速度:", "en": "Sim Speed:",
    },
    "toolbar.label.frame": {
        "zh": "帧:", "en": "Frame:",
    },

    # ---- Download Checkboxes ----
    "toolbar.cb.dl_motion": {
        "zh": "运动线图", "en": "Motion",
    },
    "toolbar.cb.dl_geom": {
        "zh": "几何约束", "en": "Geometry",
    },
    "toolbar.cb.dl_preset": {
        "zh": "预设", "en": "Preset",
    },
    "toolbar.cb.dl_s": {
        "zh": "位移", "en": "Displ.",
    },
    "toolbar.cb.dl_v": {
        "zh": "速度", "en": "Vel.",
    },
    "toolbar.cb.dl_a": {
        "zh": "加速度", "en": "Accel.",
    },
    "toolbar.cb.dl_profile": {
        "zh": "廓形图", "en": "Profile",
    },
    "toolbar.cb.dl_anim": {
        "zh": "动态图", "en": "Anim.",
    },
    "toolbar.cb.dl_excel": {
        "zh": "Excel", "en": "Excel",
    },
    "toolbar.cb.dl_alpha": {
        "zh": "压力角", "en": "Press. Angle",
    },
    "toolbar.cb.dl_curvature": {
        "zh": "曲率", "en": "Curvature",
    },
    "toolbar.cb.dl_svg": {
        "zh": "SVG", "en": "SVG",
    },
    "toolbar.cb.dl_csv": {
        "zh": "CSV", "en": "CSV",
    },

    # ---- Plot Titles ----
    "plot.title.motion": {
        "zh": r"推杆运动线图", "en": r"Follower Motion Curves",
    },
    "plot.title.geometry_constraints": {
        "zh": r"几何约束指标", "en": r"Geometry Constraints",
    },
    "plot.title.displacement": {
        "zh": r"推杆位移 $s$", "en": r"Follower Displacement $s$",
    },
    "plot.title.velocity": {
        "zh": r"推杆速度 $v$", "en": r"Follower Velocity $v$",
    },
    "plot.title.acceleration": {
        "zh": r"推杆加速度 $a$", "en": r"Follower Acceleration $a$",
    },
    "plot.title.profile": {
        "zh": r"凸轮廓形", "en": r"Cam Profile",
    },
    "plot.title.animation": {
        "zh": "凸轮动态仿真", "en": "Cam Dynamic Simulation",
    },
    "plot.title.pressure_angle": {
        "zh": r"压力角 $\alpha$", "en": r"Pressure Angle $\alpha$",
    },
    "plot.title.curvature": {
        "zh": r"曲率半径 $\rho$", "en": r"Radius of Curvature $\rho$",
    },

    # ---- Plot Legends ----
    "plot.legend.displacement": {
        "zh": "位移", "en": "Displacement",
    },
    "plot.legend.velocity": {
        "zh": "速度", "en": "Velocity",
    },
    "plot.legend.acceleration": {
        "zh": "加速度", "en": "Acceleration",
    },
    "plot.legend.pressure_angle": {
        "zh": "压力角", "en": "Pressure Angle",
    },
    "plot.legend.curvature": {
        "zh": "曲率半径", "en": "Curvature Radius",
    },
    "plot.legend.profile": {
        "zh": "廓形", "en": "Profile",
    },
    "plot.legend.base_circle": {
        "zh": "基圆", "en": "Base Circle",
    },
    "plot.legend.offset_circle": {
        "zh": "偏距圆", "en": "Offset Circle",
    },
    "plot.legend.roller_profile": {
        "zh": "实际廓形", "en": "Actual Profile",
    },
    "plot.legend.min_curvature": {
        "zh": "最小曲率半径", "en": "Min Curvature Radius",
    },

    # ---- Plot Subtitle ----
    "plot.subtitle.rise": {
        "zh": "推程", "en": "Rise",
    },
    "plot.subtitle.return": {
        "zh": "回程", "en": "Return",
    },

    # ---- Info Panel Labels ----
    "info.label.delta": {
        "zh": r"转角 $\delta$", "en": r"Angle $\delta$",
    },
    "info.label.alpha": {
        "zh": r"压力角 $\alpha$", "en": r"Pressure Angle $\alpha$",
    },
    "info.label.s": {
        "zh": r"位移 $s$", "en": r"Displacement $s$",
    },
    "info.label.h": {
        "zh": r"行程 $h$", "en": r"Stroke $h$",
    },
    "info.label.s0": {
        "zh": r"初始位移 $s_{0}$", "en": r"Initial Disp. $s_{0}$",
    },

    # ---- Status Bar Labels (plain text, no LaTeX) ----
    "status.label.h": {
        "zh": "行程 h", "en": "Stroke h",
    },
    "status.label.s0": {
        "zh": "初始位移 s₀", "en": "Initial Disp. s₀",
    },
    "status.label.max_alpha": {
        "zh": "最大压力角", "en": "Max Pressure Angle",
    },

    # ---- Status Messages ----
    "status.incomplete_params": {
        "zh": "请输入完整的参数数据", "en": "Please fill in all parameters",
    },
    "status.no_download_selection": {
        "zh": "请至少勾选一项要下载的图片", "en": "Select at least one item to download",
    },
    "status.run_first": {
        "zh": "请先运行仿真再下载", "en": "Run simulation first",
    },
    "status.saved": {
        "zh": "已保存: {files} → {folder}",
        "en": "Saved: {files} → {folder}",
    },
    "status.gif_exporting": {
        "zh": "GIF 正在导出中...", "en": "GIF exporting...",
    },
    "status.gif_composing": {
        "zh": "正在合成GIF...", "en": "Composing GIF...",
    },
    "status.gif_failed": {
        "zh": "GIF导出失败: {error}", "en": "GIF export failed: {error}",
    },
    "status.export_failed": {
        "zh": "导出失败: {error}", "en": "Export failed: {error}",
    },
    "status.warning_max_alpha": {
        "zh": "警告：最大压力角 {val:.1f}° 超过推荐值 {threshold:.0f}°",
        "en": "Warning: Max pressure angle {val:.1f}° exceeds {threshold:.0f}°",
    },
    "status.warning_h_gt_r0": {
        "zh": "警告：推杆行程({h:.1f})大于基圆半径({r0:.1f})，凸轮形状可能不合理",
        "en": "Warning: Stroke({h:.1f}) > base radius({r0:.1f}), cam shape may be invalid",
    },
    "status.max_alpha": {
        "zh": "最大压力角={val:.2f}°",
        "en": "Max pressure angle={val:.2f}°",
    },
    "status.angle_truncated": {
        "zh": "{name}：{raw} 已取整为 {rounded}",
        "en": "{name}: {raw} rounded to {rounded}",
    },
    "status.preset_saved": {
        "zh": "预设已保存: {file}", "en": "Preset saved: {file}",
    },
    "status.preset_loaded": {
        "zh": "预设已加载: {file}", "en": "Preset loaded: {file}",
    },
    "status.preset_save_failed": {
        "zh": "预设保存失败: {error}", "en": "Preset save failed: {error}",
    },
    "status.preset_load_failed": {
        "zh": "预设加载失败: {error}", "en": "Preset load failed: {error}",
    },
    "status.warning_min_curvature": {
        "zh": "警告：最小曲率半径 {val:.2f} mm 小于滚子半径 {r_r:.1f} mm，可能发生干涉",
        "en": "Warning: Min curvature radius {val:.2f} mm < roller radius {r_r:.1f} mm, interference possible",
    },
    "status.warning_r_r_negative": {
        "zh": "警告：滚子半径 {val:.1f} mm 为负值，已自动设为 0",
        "en": "Warning: Roller radius {val:.1f} mm is negative, automatically set to 0",
    },
    "status.warning_r_r_exceed": {
        "zh": "错误：滚子半径 {r_r:.1f} mm 超过最小曲率半径绝对值 {min_rho:.2f} mm，无法生成实际廓形",
        "en": "Error: Roller radius {r_r:.1f} mm exceeds min |curvature radius| {min_rho:.2f} mm, cannot generate actual profile",
    },
    "status.input_invalid": {
        "zh": "输入无效: {error}", "en": "Invalid input: {error}",
    },

    # ---- Error Keys (returned by cam_mechanics.validate_params) ----
    "error.angles_sum": {
        "zh": "四角之和必须为360°", "en": "Four angles must sum to 360°",
    },
    "error.angle_integer": {
        "zh": "{name}必须为整数", "en": "{name} must be an integer",
    },
    "error.angle_min": {
        "zh": "{name}必须>1°", "en": "{name} must be >1°",
    },
    "error.h_positive": {
        "zh": "推杆最大位移必须大于0", "en": "Max displacement must be > 0",
    },
    "error.r0_positive": {
        "zh": "基圆半径必须大于0", "en": "Base circle radius must be > 0",
    },
    "error.omega_positive": {
        "zh": "凸轮角速度必须大于0", "en": "Angular velocity must be > 0",
    },
    "error.e_negative": {
        "zh": "偏距不能为负值", "en": "Offset must not be negative",
    },
    "error.e_lt_r0": {
        "zh": "偏距必须小于基圆半径", "en": "Offset must be less than base radius",
    },
    "error.unknown_law": {
        "zh": "未知的运动规律编号: {law}", "en": "Unknown motion law ID: {law}",
    },
    "error.openpyxl_missing": {
        "zh": "Excel导出需要openpyxl：pip install openpyxl",
        "en": "Excel export requires openpyxl: pip install openpyxl",
    },

    # ---- Plot Title Law Format ----
    "plot.title.law_format": {
        "zh": "（{rise}:{tc} {ret}:{hc}）",
        "en": "({rise}:{tc} {ret}:{hc})",
    },

    # ---- Excel Sheet Name ----
    "excel.sheet_name": {
        "zh": "凸轮数据", "en": "CamForge",
    },

    # ---- Export Filenames (without extension) ----
    "export.filename.motion": {
        "zh": "推杆运动线图", "en": "motion_curves",
    },
    "export.filename.geometry": {
        "zh": "几何约束指标", "en": "geometry_constraints",
    },
    "export.filename.displacement": {
        "zh": "位移曲线", "en": "displacement",
    },
    "export.filename.velocity": {
        "zh": "速度曲线", "en": "velocity",
    },
    "export.filename.acceleration": {
        "zh": "加速度曲线", "en": "acceleration",
    },
    "export.filename.profile": {
        "zh": "凸轮廓形", "en": "cam_profile",
    },
    "export.filename.animation": {
        "zh": "凸轮动画", "en": "cam_animation",
    },
    "export.filename.excel": {
        "zh": "凸轮数据", "en": "cam_data",
    },
    "export.filename.pressure_angle": {
        "zh": "压力角曲线", "en": "pressure_angle",
    },
    "export.filename.curvature": {
        "zh": "曲率半径曲线", "en": "curvature_radius",
    },
    "export.filename.csv": {
        "zh": "凸轮数据", "en": "cam_data",
    },
    "export.filename.svg": {
        "zh": "凸轮综合图", "en": "cam_all",
    },
    "export.filename.preset": {
        "zh": "凸轮预设", "en": "cam_preset",
    },

    # ---- Excel Column Headers (plain text, no LaTeX) ----
    "excel.col.delta": {
        "zh": "转角 δ (°)", "en": "Angle δ (°)",
    },
    "excel.col.radius": {
        "zh": "向径 R (mm)", "en": "Radius R (mm)",
    },
    "excel.col.displacement": {
        "zh": "推杆位移 s (mm)", "en": "Displacement s (mm)",
    },
    "excel.col.velocity": {
        "zh": "推杆速度 v (mm/s)", "en": "Velocity v (mm/s)",
    },
    "excel.col.acceleration": {
        "zh": "推杆加速度 a (mm/s²)", "en": "Acceleration a (mm/s²)",
    },
    "excel.col.curvature": {
        "zh": "曲率半径 ρ (mm)", "en": "Curvature ρ (mm)",
    },
    "excel.col.pressure_angle": {
        "zh": "压力角 α (°)", "en": "Pressure Angle α (°)",
    },

    # ---- GIF Export Dialog ----
    "export.gif_dialog.title": {
        "zh": "导出GIF", "en": "Export GIF",
    },
    "export.gif_dialog.message": {
        "zh": "正在生成动态图GIF，请稍候...", "en": "Generating animation GIF...",
    },
    "export.folder_dialog.title": {
        "zh": "选择保存文件夹", "en": "Select Save Folder",
    },
    "export.preset_dialog.save_title": {
        "zh": "保存参数预设", "en": "Save Parameter Preset",
    },
    "export.preset_dialog.load_title": {
        "zh": "加载参数预设", "en": "Load Parameter Preset",
    },

    # ---- Motion Law Names ----
    "law.1": {"zh": "等速运动", "en": "Uniform"},
    "law.2": {"zh": "等加速等减速", "en": "Const. Accel./Decel."},
    "law.3": {"zh": "简谐运动", "en": "Simple Harmonic"},
    "law.4": {"zh": "摆线运动", "en": "Cycloidal"},
    "law.5": {"zh": "五次多项式", "en": "Quintic Polynomial"},

    # ---- Motion Law Combobox Items (sidebar, with 规律 suffix for zh) ----
    "law.combo.1": {"zh": "等速运动规律", "en": "Uniform"},
    "law.combo.2": {"zh": "等加速等减速规律", "en": "Const. Accel./Decel."},
    "law.combo.3": {"zh": "简谐运动规律", "en": "Simple Harmonic"},
    "law.combo.4": {"zh": "摆线运动规律", "en": "Cycloidal"},
    "law.combo.5": {"zh": "五次多项式运动规律", "en": "Quintic Polynomial"},

    # ---- Direction Combobox Items ----
    "dir.cw": {"zh": "顺时针", "en": "Clockwise"},
    "dir.ccw": {"zh": "逆时针", "en": "Counter-clockwise"},
    "dir.pos_offset": {"zh": "正偏距", "en": "Positive Offset"},
    "dir.neg_offset": {"zh": "负偏距", "en": "Negative Offset"},
    "theme.light": {"zh": "浅色", "en": "Light"},
    "theme.dark": {"zh": "深色", "en": "Dark"},
}


def t(key: str, lang: str, **kwargs) -> str:
    """翻译查找函数，支持格式化参数"""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return f"[{key}]"
    template = entry.get(lang)
    if template is None:
        template = entry.get(DEFAULT_LANG, f"[{key}]")
    if kwargs:
        return template.format(**kwargs)
    return template


def get_motion_law_list(lang: str) -> list:
    """获取运动规律下拉列表"""
    return [t(f"law.combo.{i}", lang) for i in range(1, 6)]


def get_rotation_list(lang: str) -> list:
    """获取旋向下拉列表"""
    return [t("dir.cw", lang), t("dir.ccw", lang)]


def get_offset_dir_list(lang: str) -> list:
    """获取偏距方向下拉列表"""
    return [t("dir.pos_offset", lang), t("dir.neg_offset", lang)]


def get_lang_display_list() -> list:
    """获取语言选择下拉列表"""
    return [LANG_DISPLAY_NAMES[code] for code in SUPPORTED_LANGS]


def detect_mpl_fonts(lang: str) -> list:
    """检测系统可用的 matplotlib 字体列表"""
    system = platform.system()
    base = list(FONT_MAP[lang]["mpl"])
    # 平台回退
    if lang == "zh":
        if system == 'Darwin':
            base += ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
        elif system != 'Windows':
            base += ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback']
    base += ['DejaVu Sans']
    return base
