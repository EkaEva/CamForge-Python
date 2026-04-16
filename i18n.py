"""
CamForge 国际化模块
支持中文(zh)、英文(en)、日文(ja)三语切换
"""

SUPPORTED_LANGS = ["zh", "en", "ja"]
DEFAULT_LANG = "zh"

LANG_DISPLAY_NAMES = {"zh": "中文", "en": "English", "ja": "日本語"}

FONT_MAP = {
    "zh": {
        "tk": "Microsoft YaHei",
        "mpl": ["SimHei", "Microsoft YaHei", "FangSong"],
    },
    "en": {
        "tk": "Segoe UI",
        "mpl": ["DejaVu Sans"],
    },
    "ja": {
        "tk": "Yu Gothic",
        "mpl": ["Yu Gothic", "Meiryo", "Hiragino Sans"],
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
        "ja": "CamForge - カムシミュレーション",
    },

    # ---- Sidebar Groups ----
    "sidebar.group.language": {
        "zh": "语言", "en": "Language", "ja": "言語",
    },
    "sidebar.group.motion": {
        "zh": "运动参数", "en": "Motion Parameters", "ja": "運動パラメータ",
    },
    "sidebar.group.geometry": {
        "zh": "几何参数", "en": "Geometry Parameters", "ja": "幾何パラメータ",
    },
    "sidebar.group.law": {
        "zh": "运动规律", "en": "Motion Laws", "ja": "運動法則",
    },
    "sidebar.group.display": {
        "zh": "动态显示", "en": "Display Options", "ja": "表示オプション",
    },

    # ---- Sidebar Labels ----
    "sidebar.label.delta_0": {
        "zh": "推程运动角 (°)", "en": "Rise Angle (°)", "ja": "上昇角 (°)",
    },
    "sidebar.label.delta_01": {
        "zh": "远休止角 (°)", "en": "Outer Dwell Angle (°)", "ja": "遠休止角 (°)",
    },
    "sidebar.label.delta_ret": {
        "zh": "回程运动角 (°)", "en": "Return Angle (°)", "ja": "復帰角 (°)",
    },
    "sidebar.label.delta_02": {
        "zh": "近休止角 (°)", "en": "Inner Dwell Angle (°)", "ja": "近休止角 (°)",
    },
    "sidebar.label.h": {
        "zh": "推杆最大位移 (mm)", "en": "Max Displacement (mm)", "ja": "フォロア最大変位 (mm)",
    },
    "sidebar.label.omega": {
        "zh": "凸轮角速度 (rad/s)", "en": "Angular Velocity (rad/s)", "ja": "カム角速度 (rad/s)",
    },
    "sidebar.label.r_0": {
        "zh": "基圆半径 (mm)", "en": "Base Circle Radius (mm)", "ja": "基礎円半径 (mm)",
    },
    "sidebar.label.e": {
        "zh": "偏距 (mm)", "en": "Offset (mm)", "ja": "オフセット (mm)",
    },
    "sidebar.label.tc_law": {
        "zh": "推程规律", "en": "Rise Law", "ja": "上昇法則",
    },
    "sidebar.label.hc_law": {
        "zh": "回程规律", "en": "Return Law", "ja": "復帰法則",
    },
    "sidebar.label.rotation": {
        "zh": "旋向", "en": "Rotation", "ja": "回転方向",
    },
    "sidebar.label.offset_dir": {
        "zh": "偏距方向", "en": "Offset Direction", "ja": "オフセット方向",
    },

    # ---- Sidebar Checkbuttons ----
    "sidebar.cb.tangent": {
        "zh": "切线", "en": "Tangent", "ja": "接線",
    },
    "sidebar.cb.normal": {
        "zh": "法线", "en": "Normal", "ja": "法線",
    },
    "sidebar.cb.arc": {
        "zh": "压力角弧线", "en": "Pressure Angle Arc", "ja": "圧力角円弧",
    },
    "sidebar.cb.boundaries": {
        "zh": "角度分界线", "en": "Phase Boundaries", "ja": "位相境界線",
    },
    "sidebar.cb.grid": {
        "zh": "网格线", "en": "Grid Lines", "ja": "グリッド線",
    },

    # ---- Toolbar Buttons ----
    "toolbar.btn.start": {
        "zh": "开始仿真", "en": "Start", "ja": "シミュレーション開始",
    },
    "toolbar.btn.pause": {
        "zh": "暂停", "en": "Pause", "ja": "一時停止",
    },
    "toolbar.btn.resume": {
        "zh": "继续", "en": "Resume", "ja": "再開",
    },
    "toolbar.btn.replay": {
        "zh": "重播", "en": "Replay", "ja": "再生",
    },
    "toolbar.btn.clear_params": {
        "zh": "清除参数", "en": "Clear Params", "ja": "パラメータクリア",
    },
    "toolbar.btn.clear_plots": {
        "zh": "清除图像", "en": "Clear Plots", "ja": "グラフクリア",
    },
    "toolbar.btn.random": {
        "zh": "随机凸轮", "en": "Random Cam", "ja": "ランダムカム",
    },
    "toolbar.btn.download": {
        "zh": "下载", "en": "Download", "ja": "ダウンロード",
    },
    "toolbar.label.speed": {
        "zh": "仿真速度:", "en": "Sim Speed:", "ja": "シミュ速度:",
    },

    # ---- Download Checkboxes ----
    "toolbar.cb.dl_s": {
        "zh": "位移", "en": "Displ.", "ja": "変位",
    },
    "toolbar.cb.dl_v": {
        "zh": "速度", "en": "Vel.", "ja": "速度",
    },
    "toolbar.cb.dl_a": {
        "zh": "加速度", "en": "Accel.", "ja": "加速度",
    },
    "toolbar.cb.dl_profile": {
        "zh": "廓形", "en": "Profile", "ja": "輪郭",
    },
    "toolbar.cb.dl_anim": {
        "zh": "动态图", "en": "Anim.", "ja": "アニメ",
    },
    "toolbar.cb.dl_excel": {
        "zh": "Excel", "en": "Excel", "ja": "Excel",
    },

    # ---- Plot Titles ----
    "plot.title.displacement": {
        "zh": r"推杆位移 $s$", "en": r"Follower Displacement $s$", "ja": r"フォロア変位 $s$",
    },
    "plot.title.velocity": {
        "zh": r"推杆速度 $v$", "en": r"Follower Velocity $v$", "ja": r"フォロア速度 $v$",
    },
    "plot.title.acceleration": {
        "zh": r"推杆加速度 $a$", "en": r"Follower Acceleration $a$", "ja": r"フォロア加速度 $a$",
    },
    "plot.title.profile": {
        "zh": r"凸轮廓形", "en": r"Cam Profile", "ja": r"カム輪郭",
    },
    "plot.title.animation": {
        "zh": "凸轮动态仿真", "en": "Cam Dynamic Simulation", "ja": "カム動的シミュレーション",
    },

    # ---- Plot Legends ----
    "plot.legend.profile": {
        "zh": "廓形", "en": "Profile", "ja": "輪郭",
    },
    "plot.legend.base_circle": {
        "zh": "基圆", "en": "Base Circle", "ja": "基礎円",
    },
    "plot.legend.offset_circle": {
        "zh": "偏距圆", "en": "Offset Circle", "ja": "オフセット円",
    },

    # ---- Plot Subtitle ----
    "plot.subtitle.rise": {
        "zh": "推程", "en": "Rise", "ja": "上昇",
    },
    "plot.subtitle.return": {
        "zh": "回程", "en": "Return", "ja": "復帰",
    },

    # ---- Info Panel Labels ----
    "info.label.delta": {
        "zh": r"转角 $\delta$", "en": r"Angle $\delta$", "ja": r"回転角 $\delta$",
    },
    "info.label.alpha": {
        "zh": r"压力角 $\alpha$", "en": r"Pressure Angle $\alpha$", "ja": r"圧力角 $\alpha$",
    },
    "info.label.s": {
        "zh": r"位移 $s$", "en": r"Displacement $s$", "ja": r"変位 $s$",
    },
    "info.label.h": {
        "zh": r"行程 $h$", "en": r"Stroke $h$", "ja": r"ストローク $h$",
    },
    "info.label.s0": {
        "zh": r"初始位移 $s_{0}$", "en": r"Initial Disp. $s_{0}$", "ja": r"初期変位 $s_{0}$",
    },

    # ---- Status Messages ----
    "status.incomplete_params": {
        "zh": "请输入完整的参数数据", "en": "Please fill in all parameters", "ja": "全てのパラメータを入力してください",
    },
    "status.no_download_selection": {
        "zh": "请至少勾选一项要下载的图片", "en": "Select at least one item to download", "ja": "少なくとも1つの項目を選択してください",
    },
    "status.run_first": {
        "zh": "请先运行仿真再下载", "en": "Run simulation first", "ja": "先にシミュレーションを実行してください",
    },
    "status.saved": {
        "zh": "已保存: {files} → {folder}",
        "en": "Saved: {files} → {folder}",
        "ja": "保存完了: {files} → {folder}",
    },
    "status.gif_exporting": {
        "zh": "GIF 正在导出中...", "en": "GIF exporting...", "ja": "GIFエクスポート中...",
    },
    "status.gif_failed": {
        "zh": "GIF导出失败: {error}", "en": "GIF export failed: {error}", "ja": "GIFエクスポート失敗: {error}",
    },
    "status.warning_max_alpha": {
        "zh": "警告：最大压力角 {val:.1f}° 超过推荐值 {threshold:.0f}°",
        "en": "Warning: Max pressure angle {val:.1f}° exceeds {threshold:.0f}°",
        "ja": "警告：最大圧力角 {val:.1f}°が推奨値 {threshold:.0f}°を超えています",
    },
    "status.warning_h_gt_r0": {
        "zh": "警告：推杆行程({h:.1f})大于基圆半径({r0:.1f})，凸轮形状可能不合理",
        "en": "Warning: Stroke({h:.1f}) > base radius({r0:.1f}), cam shape may be invalid",
        "ja": "警告：ストローク({h:.1f})が基礎円半径({r0:.1f})を超えています",
    },
    "status.max_alpha": {
        "zh": "最大压力角={val:.2f}°",
        "en": "Max pressure angle={val:.2f}°",
        "ja": "最大圧力角={val:.2f}°",
    },

    # ---- Error Keys (returned by cam_mechanics.validate_params) ----
    "error.angles_sum": {
        "zh": "四角之和必须为360°", "en": "Four angles must sum to 360°", "ja": "四つの角度の合計は360°でなければなりません",
    },
    "error.angle_integer": {
        "zh": "{name}必须为整数", "en": "{name} must be an integer", "ja": "{name}は整数でなければなりません",
    },
    "error.angle_min": {
        "zh": "{name}必须>1°", "en": "{name} must be >1°", "ja": "{name}は1°より大きくなければなりません",
    },
    "error.h_positive": {
        "zh": "推杆最大位移必须大于0", "en": "Max displacement must be > 0", "ja": "フォロア最大変位は0より大きくなければなりません",
    },
    "error.r0_positive": {
        "zh": "基圆半径必须大于0", "en": "Base circle radius must be > 0", "ja": "基礎円半径は0より大きくなければなりません",
    },
    "error.omega_positive": {
        "zh": "凸轮角速度必须大于0", "en": "Angular velocity must be > 0", "ja": "カム角速度は0より大きくなければなりません",
    },
    "error.e_lt_r0": {
        "zh": "偏距必须小于基圆半径", "en": "Offset must be less than base radius", "ja": "オフセットは基礎円半径未満でなければなりません",
    },
    "error.unknown_law": {
        "zh": "未知的运动规律编号: {law}", "en": "Unknown motion law ID: {law}", "ja": "未知の運動法則番号: {law}",
    },

    # ---- Export Filenames (without extension) ----
    "export.filename.displacement": {
        "zh": "位移曲线", "en": "displacement", "ja": "変位曲線",
    },
    "export.filename.velocity": {
        "zh": "速度曲线", "en": "velocity", "ja": "速度曲線",
    },
    "export.filename.acceleration": {
        "zh": "加速度曲线", "en": "acceleration", "ja": "加速度曲線",
    },
    "export.filename.profile": {
        "zh": "凸轮廓形", "en": "cam_profile", "ja": "カム輪郭",
    },
    "export.filename.animation": {
        "zh": "凸轮动画", "en": "cam_animation", "ja": "カムアニメーション",
    },
    "export.filename.excel": {
        "zh": "凸轮数据", "en": "cam_data", "ja": "カムデータ",
    },

    # ---- Excel Column Headers ----
    "excel.col.delta": {
        "zh": r"转角 $\delta$ (°)", "en": r"Angle $\delta$ (°)", "ja": r"回転角 $\delta$ (°)",
    },
    "excel.col.radius": {
        "zh": r"向径 $R$ (mm)", "en": r"Radius $R$ (mm)", "ja": r"動径 $R$ (mm)",
    },
    "excel.col.velocity": {
        "zh": r"推杆速度 $v$ (mm/s)", "en": r"Follower Velocity $v$ (mm/s)", "ja": r"フォロア速度 $v$ (mm/s)",
    },
    "excel.col.acceleration": {
        "zh": r"推杆加速度 $a$ (mm/s²)", "en": r"Follower Acceleration $a$ (mm/s²)", "ja": r"フォロア加速度 $a$ (mm/s²)",
    },

    # ---- GIF Export Dialog ----
    "export.gif_dialog.title": {
        "zh": "导出GIF", "en": "Export GIF", "ja": "GIFエクスポート",
    },
    "export.gif_dialog.message": {
        "zh": "正在生成动态图GIF，请稍候...", "en": "Generating animation GIF...", "ja": "アニメーションGIF生成中...",
    },
    "export.folder_dialog.title": {
        "zh": "选择保存文件夹", "en": "Select Save Folder", "ja": "保存フォルダを選択",
    },

    # ---- Motion Law Names ----
    "law.1": {"zh": "等速运动", "en": "Uniform", "ja": "等速運動"},
    "law.2": {"zh": "等加速等减速", "en": "Const. Accel./Decel.", "ja": "等加減速"},
    "law.3": {"zh": "简谐运动", "en": "Simple Harmonic", "ja": "調和運動"},
    "law.4": {"zh": "摆线运动", "en": "Cycloidal", "ja": "サイクロイド"},
    "law.5": {"zh": "五次多项式", "en": "Quintic Polynomial", "ja": "5次多項式"},

    # ---- Motion Law Combobox Items (sidebar, with 规律 suffix for zh) ----
    "law.combo.1": {"zh": "等速运动", "en": "Uniform", "ja": "等速運動"},
    "law.combo.2": {"zh": "等加速等减速", "en": "Const. Accel./Decel.", "ja": "等加減速"},
    "law.combo.3": {"zh": "简谐运动规律", "en": "Simple Harmonic", "ja": "調和運動"},
    "law.combo.4": {"zh": "摆线运动规律", "en": "Cycloidal", "ja": "サイクロイド"},
    "law.combo.5": {"zh": "五次多项式运动规律", "en": "Quintic Polynomial", "ja": "5次多項式"},

    # ---- Direction Combobox Items ----
    "dir.cw": {"zh": "顺时针", "en": "Clockwise", "ja": "時計回り"},
    "dir.ccw": {"zh": "逆时针", "en": "Counter-clockwise", "ja": "反時計回り"},
    "dir.pos_offset": {"zh": "正偏距", "en": "Positive Offset", "ja": "正オフセット"},
    "dir.neg_offset": {"zh": "负偏距", "en": "Negative Offset", "ja": "負オフセット"},
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
    import platform
    system = platform.system()
    base = list(FONT_MAP[lang]["mpl"])
    # 平台回退
    if lang == "zh":
        if system == 'Darwin':
            base += ['PingFang SC', 'Heiti SC', 'STHeiti', 'Arial Unicode MS']
        elif system != 'Windows':
            base += ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback']
    elif lang == "ja":
        if system == 'Darwin':
            base += ['Hiragino Sans', 'Arial Unicode MS']
        elif system != 'Windows':
            base += ['Noto Sans CJK JP', 'IPAGothic']
    base += ['DejaVu Sans']
    return base
