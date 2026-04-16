"""
CamForge - 尖顶凸轮仿真
使用 tkinter + matplotlib 实现凸轮机构运动学仿真
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import random as _random
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

from cam_mechanics import (
    compute_full_motion, compute_cam_profile, compute_pressure_angle,
    compute_rotated_cam, compute_anim_frame_data,
    compute_pressure_angle_arc, validate_params,
    DEG2RAD,
)

from i18n import t, SUPPORTED_LANGS, DEFAULT_LANG, FONT_MAP, LANG_DISPLAY_NAMES, get_motion_law_list, get_rotation_list, get_offset_dir_list, get_lang_display_list, detect_mpl_fonts

import sys
import platform

plt.rcParams['font.sans-serif'] = detect_mpl_fonts(DEFAULT_LANG)
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------------------------
# 渲染常量
# ---------------------------------------------------------------------------
TIP_WIDTH_RATIO = 0.04       # 推杆尖顶半宽与基圆半径之比
TIP_HEIGHT_RATIO = 0.08      # 推杆尖顶高度与基圆半径之比
ROD_LENGTH_RATIO = 4.0       # 推杆杆身长度与基圆半径之比
LIMIT_LINE_RATIO = 3.0       # 推杆上下限线半宽与基圆半径之比
ARC_RADIUS_RATIO = 0.3       # 压力角弧线半径与基圆半径之比
SUPPORT_SIZE_RATIO = 0.12     # 固定铰支座尺寸与基圆半径之比
MAX_PRESSURE_ANGLE = 30.0    # 压力角推荐阈值（度）
ANIM_FRAME_SKIP = 2          # 动画每N帧刷新一次画布
ANIM_MIN_DELAY_MS = 20       # 动画最小帧间隔（毫秒）
ANIM_BASE_DELAY_MS = 200     # 动画基准帧间隔（毫秒，速度=1时）
GIF_DURATION_MS = 30         # GIF 每帧时长（毫秒）
GIF_DPI = 150                # GIF 导出 DPI
STATIC_DPI = 600             # 静态图导出 DPI


def draw_fixed_support(ax, r_0):
    """在凸轮旋转中心 (0,0) 绘制固定铰支座符号（小圆圈 + 三角形 + 底座 + 斜线）"""
    sz = r_0 * SUPPORT_SIZE_RATIO
    # 三角形顶点：顶点在原点下方，底边在更下方
    tri_top_y = -sz * 0.15
    tri_bot_y = -sz * 1.35
    tri_x = [0, -sz, sz, 0]
    tri_y = [tri_top_y, tri_bot_y, tri_bot_y, tri_top_y]
    ax.fill(tri_x, tri_y, color='#555555', zorder=5)
    ax.plot(tri_x, tri_y, 'k-', linewidth=1, zorder=5)
    # 铰链小圆圈
    circle_r = sz * 0.2
    circle = plt.Circle((0, 0), circle_r, fill=False, edgecolor='k',
                         linewidth=1, zorder=6)
    ax.add_patch(circle)
    # 底座横线
    base_y = tri_bot_y
    hw = sz * 1.3
    ax.plot([-hw, hw], [base_y, base_y], 'k-', linewidth=1.5, zorder=5)
    # 斜线阴影（5条）
    n_hatch = 5
    hatch_len = sz * 0.5
    for j in range(n_hatch):
        x0 = -hw + (2 * hw) * (j + 0.5) / n_hatch
        ax.plot([x0, x0 - hatch_len * 0.6], [base_y, base_y - hatch_len],
                'k-', linewidth=0.8, zorder=5)


def generate_random_params():
    """生成随机凸轮参数（返回实际符号值 sn=±1, pz=±1）"""
    while True:
        af = _random.randint(1, 33) * 10
        bf = _random.randint(1, 34 - af // 10) * 10
        cf = _random.randint(1, 35 - af // 10 - bf // 10) * 10
        df = 360 - af - bf - cf
        if af >= 40 and bf >= 40 and cf >= 40 and df >= 40:
            break

    ff = _random.randint(10, 100)   # 基圆半径（最小10，避免极端值）
    gf = _random.randint(0, ff - 1)  # 偏距（允许0=对心）
    ef = _random.randint(1, ff)   # 推杆最大位移
    hf = _random.randint(1, 100)   # 角速度
    tc_law = _random.randint(1, 5)
    hc_law = _random.randint(1, 5)
    sn = 1 if _random.randint(1, 2) == 1 else -1
    pz = 1 if _random.randint(1, 2) == 1 else -1

    return {
        'delta_0': af, 'delta_01': bf,
        'delta_ret': cf, 'delta_02': df,
        'h': ef, 'r_0': ff, 'e': gf, 'omega': hf,
        'tc_law': tc_law, 'hc_law': hc_law,
        'sn': sn, 'pz': pz,
    }


class CamSimulator:
    """凸轮机构仿真主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(t("app.title", DEFAULT_LANG))

        self.lang = DEFAULT_LANG
        self._tk_font_family = FONT_MAP[DEFAULT_LANG]["tk"]
        self._translatable = {}  # key -> (widget, font_size)
        self._pause_state = "paused"

        # 跨平台窗口最大化
        if platform.system() == 'Windows':
            try:
                self.root.state('zoomed')
            except tk.TclError:
                self.root.geometry("1400x800")
        elif platform.system() == 'Darwin':
            self.root.attributes('-fullscreen', True)
        else:
            self.root.attributes('-zoomed', True)

        # 动画控制
        self.animating = False
        self.paused = False
        self.anim_id = None
        self.current_frame = 0

        # 预计算缓存
        self.sim_data = None
        self._anim_artists = None

        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 键盘快捷键
        self.root.bind('<Return>', lambda e: self._on_start())
        self.root.bind('<space>', lambda e: self._on_pause())
        self.root.bind('<r>', lambda e: self._on_random())

        self._build_gui()

        # 延迟刷新侧边栏，确保初始内容正确显示
        self.root.after(50, self._refresh_sidebar)

    # ===================================================================
    # i18n helpers
    # ===================================================================

    def _reg(self, key, widget, font_size=None):
        """Register a widget for language-switch updates"""
        self._translatable[key] = (widget, font_size)

    def _law_name(self, law_id):
        """Get motion law name in current language"""
        return t(f"law.{law_id}", self.lang)

    def _on_language_change(self, event=None):
        """Handle language switch"""
        idx = self.popup_lang.current()
        new_lang = SUPPORTED_LANGS[idx]
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self._tk_font_family = FONT_MAP[new_lang]["tk"]
        self._apply_language()
        self._update_mpl_fonts(new_lang)
        if self.sim_data is not None:
            self._plot_static()
            if self._anim_artists is not None:
                self._init_info_panel()
                self.ax_anim.set_title(t("plot.title.animation", self.lang), fontsize=12)
                self.canvas.draw_idle()

    def _apply_language(self):
        """Update all registered widgets for current language"""
        for key, (widget, font_size) in self._translatable.items():
            text = t(key, self.lang)
            try:
                widget.config(text=text)
            except tk.TclError:
                pass
            if font_size is not None:
                try:
                    widget.config(font=(self._tk_font_family, font_size))
                except tk.TclError:
                    pass
        # Update combobox values (preserve current index)
        tc_idx = self.popup_tc.current()
        hc_idx = self.popup_hc.current()
        sn_idx = self.popup_sn.current()
        pz_idx = self.popup_pz.current()
        self.popup_tc.config(values=get_motion_law_list(self.lang))
        self.popup_hc.config(values=get_motion_law_list(self.lang))
        self.popup_sn.config(values=get_rotation_list(self.lang))
        self.popup_pz.config(values=get_offset_dir_list(self.lang))
        self.popup_tc.current(tc_idx)
        self.popup_hc.current(hc_idx)
        self.popup_sn.current(sn_idx)
        self.popup_pz.current(pz_idx)
        self.root.title(t("app.title", self.lang))

    def _update_mpl_fonts(self, lang):
        """Update matplotlib font config"""
        plt.rcParams['font.sans-serif'] = detect_mpl_fonts(lang)
        plt.rcParams['axes.unicode_minus'] = False

    # ===================================================================
    # GUI 构建
    # ===================================================================

    def _build_gui(self):
        # ---- 整体布局：左侧边栏（可滚动） + 右侧主区域 ----
        sidebar_outer = tk.Frame(self.root, width=280, bg='#f8fafc',
                                 highlightbackground='#e2e8f0', highlightthickness=1)
        sidebar_outer.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_outer.pack_propagate(False)

        # 可滚动侧边栏：Canvas + Scrollbar + 内部Frame
        self._sb_canvas = tk.Canvas(sidebar_outer, bg='#f8fafc', highlightthickness=0, width=260)
        sb_scrollbar = tk.Scrollbar(sidebar_outer, orient=tk.VERTICAL, command=self._sb_canvas.yview)
        sb_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._sb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(self._sb_canvas, bg='#f8fafc')
        self._sb_win = self._sb_canvas.create_window(0, 0, window=sidebar, anchor='nw')

        sidebar.bind('<Configure>', self._on_sidebar_configure)
        self._sb_canvas.configure(yscrollcommand=sb_scrollbar.set)

        # 鼠标滚轮绑定（仅悬停时，跨平台兼容）
        self._sb_canvas.bind('<Enter>', self._bind_mousewheel)
        self._sb_canvas.bind('<Leave>', self._unbind_mousewheel)

        main_area = tk.Frame(self.root)
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---- 侧边栏 ----
        lbl_font = (self._tk_font_family, 10)
        ent_font = (self._tk_font_family, 10)
        lbl_kw = {'font': lbl_font, 'bg': '#f8fafc', 'anchor': 'w'}
        ent_kw = {'font': ent_font, 'width': 14}

        # Logo
        tk.Label(sidebar, text="CamForge", font=(self._tk_font_family, 16, 'bold'),
                 fg='#2563eb', bg='#f8fafc', anchor='w').pack(fill=tk.X, padx=16, pady=(16, 20))

        # ---- 语言选择组 ----
        self._sidebar_group(sidebar, t("sidebar.group.language", self.lang), i18n_key="sidebar.group.language")
        self.popup_lang = ttk.Combobox(sidebar, values=get_lang_display_list(), state='readonly', width=14)
        self.popup_lang.current(SUPPORTED_LANGS.index(DEFAULT_LANG))
        self.popup_lang.pack(fill=tk.X, padx=16, pady=(0, 8))
        self.popup_lang.bind('<<ComboboxSelected>>', self._on_language_change)

        # ---- 运动参数组 ----
        self._sidebar_group(sidebar, t("sidebar.group.motion", self.lang), i18n_key="sidebar.group.motion")

        self._sidebar_item(sidebar, t("sidebar.label.delta_0", self.lang), lbl_kw, i18n_key="sidebar.label.delta_0")
        self.entry_delta_0 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_0.insert(0, "90")
        self.entry_delta_0.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.delta_01", self.lang), lbl_kw, i18n_key="sidebar.label.delta_01")
        self.entry_delta_01 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_01.insert(0, "60")
        self.entry_delta_01.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.delta_ret", self.lang), lbl_kw, i18n_key="sidebar.label.delta_ret")
        self.entry_delta_ret = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_ret.insert(0, "120")
        self.entry_delta_ret.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.delta_02", self.lang), lbl_kw, i18n_key="sidebar.label.delta_02")
        self.entry_delta_02 = tk.Entry(sidebar, **ent_kw)
        self.entry_delta_02.insert(0, "90")
        self.entry_delta_02.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.h", self.lang), lbl_kw, i18n_key="sidebar.label.h")
        self.entry_h = tk.Entry(sidebar, **ent_kw)
        self.entry_h.insert(0, "10")
        self.entry_h.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.omega", self.lang), lbl_kw, i18n_key="sidebar.label.omega")
        self.entry_omega = tk.Entry(sidebar, **ent_kw)
        self.entry_omega.insert(0, "1")
        self.entry_omega.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 几何参数组 ----
        self._sidebar_group(sidebar, t("sidebar.group.geometry", self.lang), i18n_key="sidebar.group.geometry")

        self._sidebar_item(sidebar, t("sidebar.label.r_0", self.lang), lbl_kw, i18n_key="sidebar.label.r_0")
        self.entry_r0 = tk.Entry(sidebar, **ent_kw)
        self.entry_r0.insert(0, "40")
        self.entry_r0.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.e", self.lang), lbl_kw, i18n_key="sidebar.label.e")
        self.entry_e = tk.Entry(sidebar, **ent_kw)
        self.entry_e.insert(0, "5")
        self.entry_e.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 运动规律组 ----
        self._sidebar_group(sidebar, t("sidebar.group.law", self.lang), i18n_key="sidebar.group.law")

        motion_laws = get_motion_law_list(self.lang)
        combo_kw = {'state': 'readonly', 'width': 14}

        self._sidebar_item(sidebar, t("sidebar.label.tc_law", self.lang), lbl_kw, i18n_key="sidebar.label.tc_law")
        self.popup_tc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_tc.current(0)
        self.popup_tc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.hc_law", self.lang), lbl_kw, i18n_key="sidebar.label.hc_law")
        self.popup_hc = ttk.Combobox(sidebar, values=motion_laws, **combo_kw)
        self.popup_hc.current(0)
        self.popup_hc.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.rotation", self.lang), lbl_kw, i18n_key="sidebar.label.rotation")
        self.popup_sn = ttk.Combobox(sidebar, values=get_rotation_list(self.lang), **combo_kw)
        self.popup_sn.current(0)
        self.popup_sn.pack(fill=tk.X, padx=16, pady=(0, 8))

        self._sidebar_item(sidebar, t("sidebar.label.offset_dir", self.lang), lbl_kw, i18n_key="sidebar.label.offset_dir")
        self.popup_pz = ttk.Combobox(sidebar, values=get_offset_dir_list(self.lang), **combo_kw)
        self.popup_pz.current(0)
        self.popup_pz.pack(fill=tk.X, padx=16, pady=(0, 8))

        # ---- 动态显示组 ----
        self._sidebar_group(sidebar, t("sidebar.group.display", self.lang), i18n_key="sidebar.group.display")

        cb_kw = {'font': (self._tk_font_family, 10), 'anchor': 'w', 'bg': '#f8fafc'}

        self.show_tangent = tk.BooleanVar(value=False)
        cb_tangent = tk.Checkbutton(sidebar, text=t("sidebar.cb.tangent", self.lang), variable=self.show_tangent,
                       **cb_kw)
        cb_tangent.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.tangent", cb_tangent, font_size=10)

        self.show_normal = tk.BooleanVar(value=False)
        cb_normal = tk.Checkbutton(sidebar, text=t("sidebar.cb.normal", self.lang), variable=self.show_normal,
                       **cb_kw)
        cb_normal.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.normal", cb_normal, font_size=10)

        self.show_arc = tk.BooleanVar(value=False)
        cb_arc = tk.Checkbutton(sidebar, text=t("sidebar.cb.arc", self.lang), variable=self.show_arc,
                       command=self._on_arc_toggle, **cb_kw)
        cb_arc.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.arc", cb_arc, font_size=10)

        self.show_boundaries = tk.BooleanVar(value=False)
        cb_boundaries = tk.Checkbutton(sidebar, text=t("sidebar.cb.boundaries", self.lang), variable=self.show_boundaries,
                       **cb_kw)
        cb_boundaries.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.boundaries", cb_boundaries, font_size=10)

        self.show_base_circle = tk.BooleanVar(value=False)
        cb_base_circle = tk.Checkbutton(sidebar, text=t("sidebar.cb.base_circle", self.lang), variable=self.show_base_circle,
                       **cb_kw)
        cb_base_circle.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.base_circle", cb_base_circle, font_size=10)

        self.show_offset_circle = tk.BooleanVar(value=False)
        cb_offset_circle = tk.Checkbutton(sidebar, text=t("sidebar.cb.offset_circle", self.lang), variable=self.show_offset_circle,
                       **cb_kw)
        cb_offset_circle.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.offset_circle", cb_offset_circle, font_size=10)

        self.show_limits = tk.BooleanVar(value=False)
        cb_limits = tk.Checkbutton(sidebar, text=t("sidebar.cb.limits", self.lang), variable=self.show_limits,
                       **cb_kw)
        cb_limits.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.limits", cb_limits, font_size=10)

        self.show_grid = tk.BooleanVar(value=False)
        cb_grid = tk.Checkbutton(sidebar, text=t("sidebar.cb.grid", self.lang), variable=self.show_grid,
                       command=self._on_grid_toggle, **cb_kw)
        cb_grid.pack(fill=tk.X, padx=16, pady=1)
        self._reg("sidebar.cb.grid", cb_grid, font_size=10)

        # ---- 右侧主区域：按钮 + 图表 ----
        # 按钮栏
        toolbar = tk.Frame(main_area, bg='#ffffff', pady=6)
        toolbar.pack(fill=tk.X, padx=12, pady=(8, 0))

        btn_kw = {'font': (self._tk_font_family, 10), 'width': 10, 'height': 1,
                  'relief': tk.FLAT, 'cursor': 'hand2', 'bd': 0}

        self.btn_start = tk.Button(toolbar, text=t("toolbar.btn.start", self.lang), command=self._on_start,
                                   bg='#10b981', fg='white', activebackground='#059669',
                                   **btn_kw)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))
        self._reg("toolbar.btn.start", self.btn_start, font_size=10)

        self.btn_pause = tk.Button(toolbar, text=t("toolbar.btn.pause", self.lang), command=self._on_pause,
                                   bg='#f59e0b', fg='white', activebackground='#d97706',
                                   **btn_kw)
        self.btn_pause.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.pause", self.btn_pause, font_size=10)

        self.btn_clear_params = tk.Button(toolbar, text=t("toolbar.btn.clear_params", self.lang),
                                          command=self._on_clear_params,
                                          bg='#64748b', fg='white',
                                          activebackground='#475569',
                                          relief=tk.FLAT, bd=0,
                                          font=(self._tk_font_family, 10), width=10, height=1,
                                          cursor='hand2')
        self.btn_clear_params.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.clear_params", self.btn_clear_params, font_size=10)

        self.btn_clear_plots = tk.Button(toolbar, text=t("toolbar.btn.clear_plots", self.lang),
                                         command=self._on_clear_plots,
                                         bg='#94a3b8', fg='white',
                                         activebackground='#64748b',
                                         relief=tk.FLAT, bd=0,
                                         font=(self._tk_font_family, 10), width=10, height=1,
                                         cursor='hand2')
        self.btn_clear_plots.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.clear_plots", self.btn_clear_plots, font_size=10)

        self.btn_random = tk.Button(toolbar, text=t("toolbar.btn.random", self.lang),
                                    command=self._on_random,
                                    bg='#8b5cf6', fg='white',
                                    activebackground='#7c3aed',
                                    relief=tk.FLAT, bd=0,
                                    font=(self._tk_font_family, 10), width=10, height=1,
                                    cursor='hand2')
        self.btn_random.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.random", self.btn_random, font_size=10)

        self.btn_download = tk.Button(toolbar, text=t("toolbar.btn.download", self.lang),
                                      command=self._on_download,
                                      bg='#2563eb', fg='white',
                                      activebackground='#1d4ed8',
                                      relief=tk.FLAT, bd=0,
                                      font=(self._tk_font_family, 10), width=10, height=1,
                                      cursor='hand2')
        self.btn_download.pack(side=tk.LEFT, padx=6)
        self._reg("toolbar.btn.download", self.btn_download, font_size=10)

        # 下载勾选项
        dl_cb_kw = {'font': (self._tk_font_family, 9), 'bg': '#ffffff', 'anchor': 'w'}
        self.dl_s = tk.BooleanVar(value=True)
        cb_dl_s = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_s", self.lang), variable=self.dl_s, **dl_cb_kw)
        cb_dl_s.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_s", cb_dl_s, font_size=9)
        self.dl_v = tk.BooleanVar(value=True)
        cb_dl_v = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_v", self.lang), variable=self.dl_v, **dl_cb_kw)
        cb_dl_v.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_v", cb_dl_v, font_size=9)
        self.dl_a = tk.BooleanVar(value=True)
        cb_dl_a = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_a", self.lang), variable=self.dl_a, **dl_cb_kw)
        cb_dl_a.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_a", cb_dl_a, font_size=9)
        self.dl_profile = tk.BooleanVar(value=True)
        cb_dl_profile = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_profile", self.lang), variable=self.dl_profile, **dl_cb_kw)
        cb_dl_profile.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_profile", cb_dl_profile, font_size=9)
        self.dl_anim = tk.BooleanVar(value=True)
        cb_dl_anim = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_anim", self.lang), variable=self.dl_anim, **dl_cb_kw)
        cb_dl_anim.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_anim", cb_dl_anim, font_size=9)
        self.dl_excel = tk.BooleanVar(value=True)
        cb_dl_excel = tk.Checkbutton(toolbar, text=t("toolbar.cb.dl_excel", self.lang), variable=self.dl_excel, **dl_cb_kw)
        cb_dl_excel.pack(side=tk.LEFT, padx=2)
        self._reg("toolbar.cb.dl_excel", cb_dl_excel, font_size=9)

        # 速度滑块（靠右，标签在左滑块在右）
        speed_frame = tk.Frame(toolbar, bg='#ffffff')
        speed_frame.pack(side=tk.RIGHT, padx=(0, 8))
        lbl_speed = tk.Label(speed_frame, text=t("toolbar.label.speed", self.lang), font=(self._tk_font_family, 10),
                 bg='#ffffff')
        lbl_speed.pack(side=tk.LEFT, padx=(0, 4))
        self._reg("toolbar.label.speed", lbl_speed, font_size=10)
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                    variable=self.speed_var, length=120,
                                    font=(self._tk_font_family, 9), bg='#ffffff',
                                    highlightthickness=0)
        self.speed_scale.pack(side=tk.LEFT)

        # 状态/警告行
        status_bar = tk.Frame(main_area, bg='#ffffff')
        status_bar.pack(fill=tk.X, padx=12, pady=(2, 0))

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(status_bar, textvariable=self.status_var, fg='#ef4444',
                                     font=(self._tk_font_family, 10), anchor='w', bg='#ffffff')
        self.status_label.pack(side=tk.LEFT)

        self.alpha_var = tk.StringVar()
        self.alpha_label = tk.Label(status_bar, textvariable=self.alpha_var,
                                    font=(self._tk_font_family, 11, 'bold'), anchor='w', bg='#ffffff')
        self.alpha_label.pack(side=tk.LEFT, padx=16)

        # ---- 图表区 ----
        self.fig = Figure(figsize=(14, 7), dpi=100)

        gs = GridSpec(2, 3, figure=self.fig,
                      left=0.05, right=0.82, top=0.95, bottom=0.08,
                      wspace=0.30, hspace=0.35,
                      width_ratios=[1, 1, 1.6])

        self.ax_s = self.fig.add_subplot(gs[0, 0])
        self.ax_v = self.fig.add_subplot(gs[0, 1])
        self.ax_a = self.fig.add_subplot(gs[1, 0])
        self.ax_profile = self.fig.add_subplot(gs[1, 1])
        self.ax_anim = self.fig.add_subplot(gs[:, 2])

        # 信息面板：紧贴动态图右侧，上下对齐
        self.ax_info = self.fig.add_axes([0.83, 0.08, 0.14, 0.87])
        self.ax_info.set_xticks([])
        self.ax_info.set_yticks([])
        self.ax_info.set_frame_on(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=main_area)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def _on_sidebar_configure(self, event):
        """侧边栏内容变化时更新滚动区域"""
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _on_mousewheel(self, event):
        """鼠标滚轮滚动侧边栏（跨平台）"""
        if platform.system() == 'Darwin':
            # macOS: delta 直接为滚动量
            self._sb_canvas.yview_scroll(int(-1 * event.delta), 'units')
        elif platform.system() == 'Linux':
            # Linux: Button-4/5 事件，delta 为 120/-120
            self._sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        else:
            # Windows: delta 为 120 的倍数
            self._sb_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def _bind_mousewheel(self, event):
        """绑定鼠标滚轮事件（跨平台）"""
        self._sb_canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        # Linux 使用 Button-4/5 事件
        if platform.system() == 'Linux':
            self._sb_canvas.bind_all('<Button-4>', lambda e: self._sb_canvas.yview_scroll(-1, 'units'))
            self._sb_canvas.bind_all('<Button-5>', lambda e: self._sb_canvas.yview_scroll(1, 'units'))

    def _unbind_mousewheel(self, event):
        """解绑鼠标滚轮事件（跨平台）"""
        self._sb_canvas.unbind_all('<MouseWheel>')
        if platform.system() == 'Linux':
            self._sb_canvas.unbind_all('<Button-4>')
            self._sb_canvas.unbind_all('<Button-5>')

    def _refresh_sidebar(self):
        """强制刷新侧边栏显示"""
        self._sb_canvas.update_idletasks()
        self._sb_canvas.configure(scrollregion=self._sb_canvas.bbox('all'))
        self._sb_canvas.itemconfig(self._sb_win, width=self._sb_canvas.winfo_width())

    def _sidebar_group(self, parent, title, i18n_key=None):
        """侧边栏分组标题"""
        frame = tk.Frame(parent, bg='#f8fafc')
        frame.pack(fill=tk.X, padx=16, pady=(12, 4))
        lbl = tk.Label(frame, text=title, font=(self._tk_font_family, 9),
                 fg='#64748b', bg='#f8fafc', anchor='w')
        lbl.pack(fill=tk.X)
        tk.Frame(frame, height=1, bg='#e2e8f0').pack(fill=tk.X, pady=(2, 0))
        if i18n_key:
            self._reg(i18n_key, lbl, font_size=9)

    def _sidebar_item(self, parent, text, lbl_kw, i18n_key=None):
        """侧边栏参数标签"""
        lbl = tk.Label(parent, text=text, **lbl_kw)
        lbl.pack(fill=tk.X, padx=16, pady=(4, 0))
        if i18n_key:
            self._reg(i18n_key, lbl, font_size=10)

    # ===================================================================
    # 参数读取与校验
    # ===================================================================

    def _read_params(self):
        """读取并校验参数，返回 dict 或 None"""
        try:
            vals = {
                'delta_0': int(float(self.entry_delta_0.get())),
                'delta_01': int(float(self.entry_delta_01.get())),
                'delta_ret': int(float(self.entry_delta_ret.get())),
                'delta_02': int(float(self.entry_delta_02.get())),
                'h': float(self.entry_h.get()),
                'r_0': float(self.entry_r0.get()),
                'e': float(self.entry_e.get()),
                'omega': float(self.entry_omega.get()),
            }
        except ValueError:
            self.status_var.set(t("status.incomplete_params", self.lang))
            return None

        ok, err = validate_params(
            vals['delta_0'], vals['delta_01'], vals['delta_ret'], vals['delta_02'],
            vals['h'], vals['r_0'], vals['e'], vals['omega']
        )
        if not ok:
            if isinstance(err, tuple):
                key, name_key = err
                name = t(name_key, self.lang)
                self.status_var.set(t(key, self.lang, name=name))
            else:
                self.status_var.set(t(err, self.lang))
            return None

        # 读取下拉菜单
        vals['tc_law'] = self.popup_tc.current() + 1
        vals['hc_law'] = self.popup_hc.current() + 1
        vals['sn'] = 1 if self.popup_sn.current() == 0 else -1
        vals['pz'] = 1 if self.popup_pz.current() == 0 else -1
        vals['e'] = abs(vals['e'])  # 偏距取正值，方向由 pz 控制

        self.status_var.set("")
        self.alpha_var.set("")
        return vals

    # ===================================================================
    # 计算与启动
    # ===================================================================

    def _on_start(self):
        """开始仿真"""
        self._stop_animation()

        params = self._read_params()
        if params is None:
            return

        # 计算运动
        delta_deg, s, v, a, ds_ddelta, phase_bounds = compute_full_motion(
            params['delta_0'], params['delta_01'],
            params['delta_ret'], params['delta_02'],
            params['h'], params['r_0'], params['e'],
            params['omega'], params['tc_law'], params['hc_law']
        )

        # 计算凸轮廓形
        x, y, s_0 = compute_cam_profile(
            s, params['r_0'], params['e'], params['sn'], params['pz']
        )

        # 预计算基圆/偏距圆坐标
        delta_full = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        x_base = params['r_0'] * np.cos(delta_full)
        y_base = params['r_0'] * np.sin(delta_full)
        x_offset = x_base / params['r_0'] * params['e']
        y_offset = y_base / params['r_0'] * params['e']

        # 预计算 Rmax
        R = np.hypot(x, y)
        Rmax = np.max(R)

        # 解析压力角
        alpha_all = compute_pressure_angle(s, ds_ddelta, s_0, params['e'], params['pz'])
        max_alpha = np.max(np.abs(alpha_all))

        # 压力角超限警告
        if max_alpha > MAX_PRESSURE_ANGLE:
            self.status_var.set(t("status.warning_max_alpha", self.lang, val=max_alpha, threshold=MAX_PRESSURE_ANGLE))

        # 行程过大警告（h > r_0 时凸轮形状可能不合理）
        if params['h'] > params['r_0']:
            self.status_var.set(
                t("status.warning_h_gt_r0", self.lang, h=params['h'], r0=params['r_0']))

        # 保存计算结果
        self.sim_data = {
            'delta_deg': delta_deg, 's': s, 'v': v, 'a': a,
            'ds_ddelta': ds_ddelta, 'phase_bounds': phase_bounds,
            'x': x, 'y': y, 's_0': s_0,
            'r_0': params['r_0'], 'e': params['e'], 'h': params['h'],
            'omega': params['omega'], 'sn': params['sn'], 'pz': params['pz'],
            'tc_law': params['tc_law'], 'hc_law': params['hc_law'],
            'x_base': x_base, 'y_base': y_base,
            'x_offset': x_offset, 'y_offset': y_offset,
            'Rmax': Rmax, 'max_alpha': max_alpha,
            'alpha_all': alpha_all,
        }

        # 绘制静态图
        self._plot_static()

        # 开始动画
        self._start_animation()

    # ===================================================================
    # 静态图表
    # ===================================================================

    def _plot_static(self):
        """绘制静态图表"""
        data = self.sim_data
        delta_deg = data['delta_deg']
        s, v, a = data['s'], data['v'], data['a']
        pb = data['phase_bounds']
        x, y = data['x'], data['y']
        r_0, e, s_0, h = data['r_0'], data['e'], data['s_0'], data['h']
        Rmax = data['Rmax']

        # 运动规律名称
        tc_name = self._law_name(data.get('tc_law', 1))
        hc_name = self._law_name(data.get('hc_law', 1))

        for ax in [self.ax_s, self.ax_v, self.ax_a, self.ax_profile]:
            ax.clear()

        # ---- 位移图 ----
        self.ax_s.plot(delta_deg, s, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_s.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_s.set_title(
            rf'{t("plot.title.displacement", self.lang)}（{t("plot.subtitle.rise", self.lang)}:{tc_name} {t("plot.subtitle.return", self.lang)}:{hc_name}）',
            fontsize=10)
        self.ax_s.set_xlabel(r'$\delta$ (°)')
        self.ax_s.set_ylabel(r'$s$ (mm)')
        self.ax_s.set_xlim(0, 360)
        self.ax_s.set_ylim(0, h * 1.15)
        self.ax_s.set_xticks(range(0, 361, 60))
        self.ax_s.grid(True)

        # ---- 速度图 ----
        self.ax_v.plot(delta_deg, v, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_v.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_v.set_title(t("plot.title.velocity", self.lang), fontsize=11)
        self.ax_v.set_xlabel(r'$\delta$ (°)')
        self.ax_v.set_ylabel(r'$v$ (mm/s)')
        self.ax_v.set_xlim(0, 360)
        v_max = np.max(np.abs(v)) * 1.15
        if v_max > 0:
            self.ax_v.set_ylim(-v_max, v_max)
        self.ax_v.set_xticks(range(0, 361, 60))
        self.ax_v.grid(True)

        # ---- 加速度图 ----
        self.ax_a.plot(delta_deg, a, 'r-', linewidth=1.5)
        for b in pb[1:-1]:
            self.ax_a.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
        self.ax_a.set_title(t("plot.title.acceleration", self.lang), fontsize=11)
        self.ax_a.set_xlabel(r'$\delta$ (°)')
        self.ax_a.set_ylabel(r'$a$ (mm/s$^2$)')
        self.ax_a.set_xlim(0, 360)
        a_max = np.max(np.abs(a)) * 1.15
        if a_max > 0:
            self.ax_a.set_ylim(-a_max, a_max)
        self.ax_a.set_xticks(range(0, 361, 60))
        self.ax_a.grid(True)

        # ---- 凸轮廓形图 ----
        self.ax_profile.plot(x, y, 'r-', linewidth=2, label=t("plot.legend.profile", self.lang))
        self.ax_profile.plot(data['x_base'], data['y_base'],
                             'm-', linewidth=1, label=t("plot.legend.base_circle", self.lang))
        self.ax_profile.plot(data['x_offset'], data['y_offset'],
                             'c-', linewidth=1, label=t("plot.legend.offset_circle", self.lang))

        n = len(x)
        for b_deg in pb[1:-1]:
            idx = int(b_deg)
            if idx < n:
                self.ax_profile.plot([0, x[idx]], [0, y[idx]],
                                     'k-', linewidth=0.8)

        self.ax_profile.set_title(t("plot.title.profile", self.lang), fontsize=11)
        self.ax_profile.set_xlabel(r'$x$ (mm)')
        self.ax_profile.set_ylabel(r'$y$ (mm)')
        self.ax_profile.grid(True)
        draw_fixed_support(self.ax_profile, r_0)
        margin = r_0 / 2
        self.ax_profile.set_xlim(-Rmax - margin, Rmax + margin)
        self.ax_profile.set_ylim(-Rmax - r_0, Rmax + r_0)
        self.ax_profile.set_aspect('equal')
        self.ax_profile.legend(fontsize=8, loc='upper right')

        self.canvas.draw()

    # ===================================================================
    # 动画
    # ===================================================================

    def _init_anim_artists(self):
        """初始化动画图形对象（只创建一次，后续用 set_data 更新）"""
        ax = self.ax_anim
        ax.clear()

        data = self.sim_data
        r_0 = data['r_0']
        h = data['h']
        Rmax = data['Rmax']

        # 凸轮廓形
        line_cam, = ax.plot([], [], 'r-', linewidth=2)
        # 基圆（默认隐藏）
        line_base, = ax.plot([], [], 'm-', linewidth=1)
        # 偏距圆（默认隐藏）
        line_offset, = ax.plot([], [], 'c-', linewidth=1)
        # 切线
        line_tangent, = ax.plot([], [], 'm-', linewidth=1)
        # 法线
        line_normal, = ax.plot([], [], 'm-', linewidth=1)
        # 推杆杆身
        line_rod, = ax.plot([], [], 'k-', linewidth=3, solid_capstyle='butt')
        # 推杆尖顶（小三角）
        line_tip, = ax.plot([], [], 'k-', linewidth=2)
        # 推杆中心虚线（压力角弧线参考线）
        line_center, = ax.plot([], [], 'k--', linewidth=0.8)
        # 推杆下限
        line_lower, = ax.plot([], [], 'c-.', linewidth=1)
        # 推杆上限
        line_upper, = ax.plot([], [], 'm--', linewidth=1)
        # 角度分界线（最多4条）
        lines_boundary = []
        for _ in range(4):
            lb, = ax.plot([], [], 'k-', linewidth=0.8)
            lines_boundary.append(lb)
        # 压力角弧线
        line_arc, = ax.plot([], [], 'k-', linewidth=1)

        ax.set_xlim(-Rmax - h, Rmax + h)
        ax.set_ylim(-Rmax - r_0, Rmax + r_0)
        ax.set_aspect('equal')
        ax.grid(self.show_grid.get())
        ax.set_title(t("plot.title.animation", self.lang), fontsize=12)
        ax.set_xlabel(r'$x$ (mm)')
        ax.set_ylabel(r'$y$ (mm)')

        # 固定铰支座
        draw_fixed_support(ax, r_0)

        # 信息面板：紧贴动态图右侧，上下对齐
        anim_pos = ax.get_position()
        info_x0 = anim_pos.x1 + 0.01
        info_w = 0.14
        self.ax_info.set_position([info_x0, anim_pos.y0, info_w, anim_pos.y1 - anim_pos.y0])
        self._init_info_panel()

        self._anim_artists = {
            'cam': line_cam,
            'base': line_base,
            'offset': line_offset,
            'tangent': line_tangent,
            'normal': line_normal,
            'rod': line_rod,
            'tip': line_tip,
            'center': line_center,
            'lower': line_lower,
            'upper': line_upper,
            'boundaries': lines_boundary,
            'arc': line_arc,
        }

    def _init_info_panel(self):
        """初始化信息面板（独立的 ax_info，与动态图完全不重叠）"""
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)

        info_items = [
            ('delta', t("info.label.delta", self.lang)),
            ('alpha', t("info.label.alpha", self.lang)),
            ('s',     t("info.label.s", self.lang)),
            ('h',     t("info.label.h", self.lang)),
            ('s0',    t("info.label.s0", self.lang)),
        ]
        self._info_labels = {}
        for idx, (key, name) in enumerate(info_items):
            y_pos = 0.95 - idx * 0.10
            lbl = ax.text(0.05, y_pos, f'{name}: --', transform=ax.transAxes,
                          fontsize=10, ha='left', va='top', color='#222')
            self._info_labels[key] = lbl

    def _start_animation(self):
        """开始凸轮旋转动画"""
        self.animating = True
        self.paused = False
        self.current_frame = 0
        self.btn_pause.config(text=t("toolbar.btn.pause", self.lang))
        self._pause_state = "paused"
        self._init_anim_artists()
        self._animate_frame()

    def _stop_animation(self):
        """停止动画"""
        self.animating = False
        self.paused = False
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self._anim_artists = None

    def _on_pause(self):
        """暂停/继续/重播"""
        if self.animating:
            self.paused = not self.paused
            if self.paused:
                self.btn_pause.config(text=t("toolbar.btn.resume", self.lang))
                self._pause_state = "paused_running"
            else:
                self.btn_pause.config(text=t("toolbar.btn.pause", self.lang))
                self._pause_state = "paused"
                self._animate_frame()
        elif self.sim_data is not None and self._pause_state == "replay":
            self._start_animation()

    def _animate_frame(self):
        """绘制一帧动画（解析计算推杆位置，set_data 更新）"""
        if not self.animating or self.paused:
            return

        data = self.sim_data
        artists = self._anim_artists
        if artists is None:
            return

        r_0 = data['r_0']
        h = data['h']
        sn = data['sn']
        pb = data['phase_bounds']
        s = data['s']
        s_0 = data['s_0']
        e = data['e']
        pz = data['pz']
        alpha_all = data['alpha_all']

        N = len(s)
        i = self.current_frame

        if i >= N:
            self.animating = False
            self.btn_pause.config(text=t("toolbar.btn.replay", self.lang))
            self._pause_state = "replay"
            self.alpha_var.set(t("status.max_alpha", self.lang, val=data['max_alpha']))
            label_delta = t("info.label.delta", self.lang)
            label_alpha = t("info.label.alpha", self.lang)
            label_s = t("info.label.s", self.lang)
            label_h = t("info.label.h", self.lang)
            label_s0 = t("info.label.s0", self.lang)
            self._info_labels['delta'].set_text(rf'{label_delta}: 360°/360°')
            self._info_labels['alpha'].set_text(rf'{label_alpha}: {data["max_alpha"]:.2f}°')
            self._info_labels['s'].set_text(rf'{label_s}: 0.00 mm')
            self._info_labels['h'].set_text(rf'{label_h}: {h:.1f} mm')
            self._info_labels['s0'].set_text(rf'{label_s0}: {s_0:.2f} mm')
            self.canvas.draw_idle()
            return

        # ---- 凸轮旋转 ----
        angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
        x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)
        artists['cam'].set_data(x_rot, y_rot)

        # ---- 基圆 ----
        if self.show_base_circle.get():
            artists['base'].set_data(data['x_base'], data['y_base'])
        else:
            artists['base'].set_data([], [])

        # ---- 偏距圆 ----
        if self.show_offset_circle.get():
            artists['offset'].set_data(data['x_offset'], data['y_offset'])
        else:
            artists['offset'].set_data([], [])

        # ---- 解析计算帧数据 ----
        frame = compute_anim_frame_data(
            s, data['ds_ddelta'], s_0, e, r_0, sn, pz, i, alpha_all)
        follower_x = frame['follower_x']
        cy = frame['contact_y']
        cx = follower_x
        nx, ny = frame['nx'], frame['ny']
        tx, ty = frame['tx'], frame['ty']
        alpha_i = frame['alpha_i']

        # ---- 切线 ----
        if self.show_tangent.get():
            artists['tangent'].set_data(
                [cx - r_0 * tx, cx + r_0 * tx],
                [cy - r_0 * ty, cy + r_0 * ty]
            )
        else:
            artists['tangent'].set_data([], [])

        # ---- 法线 ----
        if self.show_normal.get():
            artists['normal'].set_data(
                [cx + r_0 * nx, cx - r_0 * nx],
                [cy + r_0 * ny, cy - r_0 * ny]
            )
        else:
            artists['normal'].set_data([], [])

        # ---- 推杆（杆身 + 尖顶） ----
        tip_w = r_0 * TIP_WIDTH_RATIO
        tip_h = r_0 * TIP_HEIGHT_RATIO
        rod_top = cy + r_0 * ROD_LENGTH_RATIO
        # 杆身（尖顶上方到顶部）
        artists['rod'].set_data(
            [follower_x, follower_x], [cy + tip_h, rod_top])
        # 尖顶（小三角）
        artists['tip'].set_data(
            [follower_x - tip_w, follower_x, follower_x + tip_w, follower_x - tip_w],
            [cy + tip_h, cy, cy + tip_h, cy + tip_h])

        # ---- 推杆上下限水平线 ----
        if self.show_limits.get():
            artists['lower'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0])
            artists['upper'].set_data([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h])
        else:
            artists['lower'].set_data([], [])
            artists['upper'].set_data([], [])

        # ---- 角度分界线 ----
        if self.show_boundaries.get():
            for j, lb in enumerate(artists['boundaries']):
                if j < len(pb) - 1:
                    b_deg = pb[j + 1]
                    idx = int(b_deg)
                    if idx < N:
                        lb.set_data([0, x_rot[idx]], [0, y_rot[idx]])
                    else:
                        lb.set_data([], [])
                else:
                    lb.set_data([], [])
        else:
            for lb in artists['boundaries']:
                lb.set_data([], [])

        # ---- 压力角弧线 + 中心虚线 ----
        if self.show_arc.get():
            arc_r = r_0 * ARC_RADIUS_RATIO
            x_arc, y_arc = compute_pressure_angle_arc(cx, cy, nx, ny, alpha_i, arc_r)
            artists['arc'].set_data(x_arc, y_arc)
            # 中心虚线（推杆中心延伸线，作为压力角参考）
            artists['center'].set_data(
                [follower_x, follower_x], [cy - r_0 * 2, cy + r_0 * 5])
        else:
            artists['arc'].set_data([], [])
            artists['center'].set_data([], [])

        # ---- 信息面板 ----
        label_delta = t("info.label.delta", self.lang)
        label_alpha = t("info.label.alpha", self.lang)
        label_s = t("info.label.s", self.lang)
        label_h = t("info.label.h", self.lang)
        label_s0 = t("info.label.s0", self.lang)
        self._info_labels['delta'].set_text(rf'{label_delta}: {i:3d}°/360°')
        self._info_labels['alpha'].set_text(rf'{label_alpha}: {alpha_i:.1f}°')
        self._info_labels['s'].set_text(rf'{label_s}: {frame["s_i"]:.2f} mm')
        self._info_labels['h'].set_text(rf'{label_h}: {h:.1f} mm')
        self._info_labels['s0'].set_text(rf'{label_s0}: {s_0:.2f} mm')

        # 仅每N帧刷新一次画布，减少卡顿
        if i % ANIM_FRAME_SKIP == 0:
            self.canvas.draw_idle()

        self.current_frame += 1
        # 帧间隔：指数映射，最小延迟防止卡顿
        delay = max(ANIM_MIN_DELAY_MS, int(ANIM_BASE_DELAY_MS / (self.speed_var.get() ** 1.5)))
        self.anim_id = self.root.after(delay, self._animate_frame)

    # ===================================================================
    # 按钮回调
    # ===================================================================

    def _on_arc_toggle(self):
        """勾选压力角弧线时自动开启法线，关闭时同时关闭法线并清除残留"""
        if self.show_arc.get():
            self.show_normal.set(True)
        else:
            self.show_normal.set(False)
            # 立即清除弧线、法线和中心虚线，避免残留
            if self._anim_artists:
                self._anim_artists['arc'].set_data([], [])
                self._anim_artists['normal'].set_data([], [])
                self._anim_artists['center'].set_data([], [])
                self.canvas.draw_idle()

    def _on_grid_toggle(self):
        """切换动态图网格线"""
        self.ax_anim.grid(self.show_grid.get())
        self.canvas.draw_idle()

    def _on_download(self):
        """下载勾选的图片（静态图为PNG，动态图为GIF）"""
        from tkinter import filedialog
        import os
        from io import BytesIO

        # 检查是否有勾选
        if not any([self.dl_s.get(), self.dl_v.get(), self.dl_a.get(),
                     self.dl_profile.get(), self.dl_anim.get(), self.dl_excel.get()]):
            self.status_var.set(t("status.no_download_selection", self.lang))
            return

        if self.sim_data is None:
            self.status_var.set(t("status.run_first", self.lang))
            return

        folder = filedialog.askdirectory(title=t("export.folder_dialog.title", self.lang))
        if not folder:
            return

        dpi = STATIC_DPI
        saved = []
        data = self.sim_data

        # ---- 位移曲线 ----
        if self.dl_s.get():
            delta_deg = data['delta_deg']
            s = data['s']
            pb = data['phase_bounds']
            fig_s = Figure(figsize=(6, 4), dpi=dpi)
            ax_s = fig_s.add_subplot(111)
            ax_s.plot(delta_deg, s, 'r-', linewidth=1.5)
            for b in pb[1:-1]:
                ax_s.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
            ax_s.set_title(t("plot.title.displacement", self.lang), fontsize=11)
            ax_s.set_xlabel(r'$\delta$ (°)')
            ax_s.set_ylabel(r'$s$ (mm)')
            ax_s.set_xlim(0, 360)
            ax_s.set_ylim(0, data['h'] * 1.15)
            ax_s.set_xticks(range(0, 361, 60))
            ax_s.grid(True)
            filename_s = t("export.filename.displacement", self.lang) + ".tiff"
            fig_s.savefig(os.path.join(folder, filename_s), dpi=dpi, bbox_inches='tight', format='tiff')
            plt.close(fig_s)
            saved.append(filename_s)

        # ---- 速度曲线 ----
        if self.dl_v.get():
            delta_deg = data['delta_deg']
            v = data['v']
            pb = data['phase_bounds']
            fig_v = Figure(figsize=(6, 4), dpi=dpi)
            ax_v = fig_v.add_subplot(111)
            ax_v.plot(delta_deg, v, 'r-', linewidth=1.5)
            for b in pb[1:-1]:
                ax_v.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
            ax_v.set_title(t("plot.title.velocity", self.lang), fontsize=11)
            ax_v.set_xlabel(r'$\delta$ (°)')
            ax_v.set_ylabel(r'$v$ (mm/s)')
            ax_v.set_xlim(0, 360)
            v_max = np.max(np.abs(v)) * 1.15
            if v_max > 0:
                ax_v.set_ylim(-v_max, v_max)
            ax_v.set_xticks(range(0, 361, 60))
            ax_v.grid(True)
            filename_v = t("export.filename.velocity", self.lang) + ".tiff"
            fig_v.savefig(os.path.join(folder, filename_v), dpi=dpi, bbox_inches='tight', format='tiff')
            plt.close(fig_v)
            saved.append(filename_v)

        # ---- 加速度曲线 ----
        if self.dl_a.get():
            delta_deg = data['delta_deg']
            a = data['a']
            pb = data['phase_bounds']
            fig_a = Figure(figsize=(6, 4), dpi=dpi)
            ax_a = fig_a.add_subplot(111)
            ax_a.plot(delta_deg, a, 'r-', linewidth=1.5)
            for b in pb[1:-1]:
                ax_a.axvline(x=b, color='gray', linestyle='--', linewidth=0.8)
            ax_a.set_title(t("plot.title.acceleration", self.lang), fontsize=11)
            ax_a.set_xlabel(r'$\delta$ (°)')
            ax_a.set_ylabel(r'$a$ (mm/s$^2$)')
            ax_a.set_xlim(0, 360)
            a_max = np.max(np.abs(a)) * 1.15
            if a_max > 0:
                ax_a.set_ylim(-a_max, a_max)
            ax_a.set_xticks(range(0, 361, 60))
            ax_a.grid(True)
            filename_a = t("export.filename.acceleration", self.lang) + ".tiff"
            fig_a.savefig(os.path.join(folder, filename_a), dpi=dpi, bbox_inches='tight', format='tiff')
            plt.close(fig_a)
            saved.append(filename_a)

        # ---- 凸轮廓形 ----
        if self.dl_profile.get():
            x, y = data['x'], data['y']
            r_0 = data['r_0']
            Rmax = data['Rmax']
            pb = data['phase_bounds']
            n = len(x)
            fig_p = Figure(figsize=(6, 6), dpi=dpi)
            ax_p = fig_p.add_subplot(111)
            ax_p.plot(x, y, 'r-', linewidth=2, label=t("plot.legend.profile", self.lang))
            ax_p.plot(data['x_base'], data['y_base'], 'm-', linewidth=1, label=t("plot.legend.base_circle", self.lang))
            ax_p.plot(data['x_offset'], data['y_offset'], 'c-', linewidth=1, label=t("plot.legend.offset_circle", self.lang))
            for b_deg in pb[1:-1]:
                idx = int(b_deg)
                if idx < n:
                    ax_p.plot([0, x[idx]], [0, y[idx]], 'k-', linewidth=0.8)
            ax_p.set_title(t("plot.title.profile", self.lang), fontsize=11)
            ax_p.set_xlabel(r'$x$ (mm)')
            ax_p.set_ylabel(r'$y$ (mm)')
            ax_p.grid(True)
            draw_fixed_support(ax_p, r_0)
            margin = r_0 / 2
            ax_p.set_xlim(-Rmax - margin, Rmax + margin)
            ax_p.set_ylim(-Rmax - r_0, Rmax + r_0)
            ax_p.set_aspect('equal')
            ax_p.legend(fontsize=8, loc='upper right')
            filename_p = t("export.filename.profile", self.lang) + ".tiff"
            fig_p.savefig(os.path.join(folder, filename_p), dpi=dpi, bbox_inches='tight', format='tiff')
            plt.close(fig_p)
            saved.append(filename_p)

        # ---- Excel 数据表 ----
        if self.dl_excel.get():
            self._export_excel(folder, saved)

        # 动态图：保存完整360帧为GIF（后台线程，避免UI冻结）
        if self.dl_anim.get():
            filename_anim = t("export.filename.animation", self.lang) + ".gif"
            filepath = os.path.join(folder, filename_anim)
            self._export_gif(filepath, folder, saved)

        if saved:
            self.status_var.set(t("status.saved", self.lang, files=', '.join(saved), folder=folder))
        elif self.dl_anim.get():
            self.status_var.set(t("status.gif_exporting", self.lang))

    def _export_excel(self, folder, saved_list):
        """导出凸轮数据为 Excel 表格"""
        import os
        try:
            import openpyxl
        except ImportError:
            self.status_var.set("Excel export requires openpyxl: pip install openpyxl")
            return

        data = self.sim_data
        delta_deg = data['delta_deg']
        v = data['v']
        a = data['a']
        x = data['x']
        y = data['y']
        R = np.hypot(x, y)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CamForge"

        # 表头
        headers = [
            t("excel.col.delta", self.lang),
            t("excel.col.radius", self.lang),
            t("excel.col.velocity", self.lang),
            t("excel.col.acceleration", self.lang),
        ]
        for col_idx, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_idx, value=header)

        # 数据
        for i in range(len(delta_deg)):
            ws.cell(row=i + 2, column=1, value=round(delta_deg[i], 1))
            ws.cell(row=i + 2, column=2, value=round(R[i], 4))
            ws.cell(row=i + 2, column=3, value=round(v[i], 4))
            ws.cell(row=i + 2, column=4, value=round(a[i], 4))

        # 列宽自适应
        for col in range(1, 5):
            max_len = len(str(ws.cell(row=1, column=col).value))
            for row in range(2, min(10, len(delta_deg) + 2)):
                cell_len = len(str(ws.cell(row=row, column=col).value))
                if cell_len > max_len:
                    max_len = cell_len
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max_len + 4

        filename = t("export.filename.excel", self.lang) + ".xlsx"
        filepath = os.path.join(folder, filename)
        wb.save(filepath)
        saved_list.append(filename)

    def _export_gif(self, filepath, folder, saved_list):
        """在后台线程中导出GIF动画（300 DPI），显示进度对话框"""
        import os
        import threading
        from io import BytesIO
        from PIL import Image as PILImage

        # Capture lang and display options for thread safety
        lang = self.lang
        show_base = self.show_base_circle.get()
        show_offset = self.show_offset_circle.get()
        show_limits = self.show_limits.get()
        show_tangent_gif = self.show_tangent.get()
        show_normal_gif = self.show_normal.get()
        show_arc_gif = self.show_arc.get()
        show_boundaries_gif = self.show_boundaries.get()

        data = self.sim_data
        s = data['s']
        ds_ddelta = data['ds_ddelta']
        s_0 = data['s_0']
        e = data['e']
        r_0 = data['r_0']
        h = data['h']
        sn = data['sn']
        pz = data['pz']
        alpha_all = data['alpha_all']
        pb = data['phase_bounds']
        N = len(s)
        xlim = self.ax_anim.get_xlim()
        ylim = self.ax_anim.get_ylim()

        # 进度对话框
        progress_win = tk.Toplevel(self.root)
        progress_win.title(t("export.gif_dialog.title", lang))
        progress_win.geometry("320x100")
        progress_win.resizable(False, False)
        progress_win.transient(self.root)
        progress_win.grab_set()
        tk.Label(progress_win, text=t("export.gif_dialog.message", lang),
                 font=(self._tk_font_family, 10)).pack(pady=(12, 4))
        progress_bar = ttk.Progressbar(progress_win, length=280, mode='determinate', maximum=N)
        progress_bar.pack(pady=4)
        progress_label = tk.Label(progress_win, text="0 / 360", font=(self._tk_font_family, 9))
        progress_label.pack()

        # 线程间共享状态
        gif_result = {'error': None}

        def generate():
            try:
                fig_gif = Figure(figsize=(8, 6), dpi=GIF_DPI)
                ax_gif = fig_gif.add_axes([0.05, 0.08, 0.65, 0.87])
                ax_info_gif = fig_gif.add_axes([0.73, 0.08, 0.25, 0.87])

                first_frame = None
                append_frames = []

                # Pre-compute translated labels for GIF
                label_delta_gif = t("info.label.delta", lang)
                label_alpha_gif = t("info.label.alpha", lang)
                label_s_gif = t("info.label.s", lang)
                label_h_gif = t("info.label.h", lang)
                label_s0_gif = t("info.label.s0", lang)
                title_anim_gif = t("plot.title.animation", lang)

                for i in range(N):
                    angle_rad = -i * DEG2RAD if sn == 1 else i * DEG2RAD
                    x_rot, y_rot = compute_rotated_cam(data['x'], data['y'], angle_rad)

                    ax_gif.clear()
                    ax_gif.plot(x_rot, y_rot, 'r-', linewidth=2)
                    if show_base:
                        ax_gif.plot(data['x_base'], data['y_base'], 'm-', linewidth=1)
                    if show_offset:
                        ax_gif.plot(data['x_offset'], data['y_offset'], 'c-', linewidth=1)

                    frame_data = compute_anim_frame_data(
                        s, ds_ddelta, s_0, e, r_0, sn, pz, i, alpha_all)
                    fx = frame_data['follower_x']
                    cy = frame_data['contact_y']
                    alpha_i = frame_data['alpha_i']
                    nx_i, ny_i = frame_data['nx'], frame_data['ny']
                    tx_i, ty_i = frame_data['tx'], frame_data['ty']
                    tip_w = r_0 * TIP_WIDTH_RATIO
                    tip_h = r_0 * TIP_HEIGHT_RATIO
                    ax_gif.plot([fx, fx], [cy + tip_h, cy + r_0 * ROD_LENGTH_RATIO], 'k-', linewidth=3)
                    ax_gif.plot([fx - tip_w, fx, fx + tip_w, fx - tip_w],
                                [cy + tip_h, cy, cy + tip_h, cy + tip_h], 'k-', linewidth=2)
                    if show_limits:
                        ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0, s_0], 'c-.', linewidth=1)
                        ax_gif.plot([-r_0 * LIMIT_LINE_RATIO, r_0 * LIMIT_LINE_RATIO], [s_0 + h, s_0 + h], 'm--', linewidth=1)
                    if show_tangent_gif:
                        ax_gif.plot([fx - r_0 * tx_i, fx + r_0 * tx_i],
                                    [cy - r_0 * ty_i, cy + r_0 * ty_i], 'm-', linewidth=1)
                    if show_normal_gif:
                        ax_gif.plot([fx + r_0 * nx_i, fx - r_0 * nx_i],
                                    [cy + r_0 * ny_i, cy - r_0 * ny_i], 'm-', linewidth=1)
                    if show_boundaries_gif:
                        for j_b in range(len(pb) - 1):
                            idx_b = int(pb[j_b + 1])
                            if idx_b < N:
                                ax_gif.plot([0, x_rot[idx_b]], [0, y_rot[idx_b]], 'k-', linewidth=0.8)
                    if show_arc_gif:
                        arc_r = r_0 * ARC_RADIUS_RATIO
                        x_arc, y_arc = compute_pressure_angle_arc(fx, cy, nx_i, ny_i, alpha_i, arc_r)
                        ax_gif.plot(x_arc, y_arc, 'k-', linewidth=1)
                        ax_gif.plot([fx, fx], [cy - r_0 * 2, cy + r_0 * 5], 'k--', linewidth=0.8)
                    draw_fixed_support(ax_gif, r_0)
                    ax_gif.set_xlim(xlim)
                    ax_gif.set_ylim(ylim)
                    ax_gif.set_aspect('equal')
                    ax_gif.set_title(f'{title_anim_gif}  {i:3d}°/360°', fontsize=11)

                    ax_info_gif.clear()
                    ax_info_gif.set_xticks([])
                    ax_info_gif.set_yticks([])
                    ax_info_gif.set_frame_on(False)
                    info_items = [
                        (0.95, rf'{label_delta_gif}: {i:3d}°/360°'),
                        (0.85, rf'{label_alpha_gif}: {alpha_i:.1f}°'),
                        (0.75, rf'{label_s_gif}: {frame_data["s_i"]:.2f} mm'),
                        (0.65, rf'{label_h_gif}: {h:.1f} mm'),
                        (0.55, rf'{label_s0_gif}: {s_0:.2f} mm'),
                    ]
                    for y_pos, text in info_items:
                        ax_info_gif.text(0.05, y_pos, text, transform=ax_info_gif.transAxes,
                                         fontsize=10, ha='left', va='top', color='#222')

                    buf = BytesIO()
                    fig_gif.savefig(buf, format='png', dpi=GIF_DPI)
                    buf.seek(0)
                    img = PILImage.open(buf).copy()
                    buf.close()

                    if first_frame is None:
                        first_frame = img
                    else:
                        append_frames.append(img)

                    # 更新进度（线程安全）
                    self.root.after(0, lambda idx=i: (
                        progress_bar.configure(value=idx + 1),
                        progress_label.configure(text=f"{idx + 1} / {N}")
                    ))

                plt.close(fig_gif)
                # 提示正在合成GIF
                self.root.after(0, lambda: progress_label.configure(
                    text=t("status.gif_composing", lang)))
                if first_frame is not None:
                    first_frame.save(filepath, save_all=True, append_images=append_frames,
                                     duration=GIF_DURATION_MS, loop=0)
                saved_list.append(os.path.basename(filepath))
            except Exception as exc:
                gif_result['error'] = str(exc)
            finally:
                def _on_done():
                    progress_win.destroy()
                    if gif_result['error']:
                        self.status_var.set(t("status.gif_failed", lang, error=gif_result['error']))
                    else:
                        self.status_var.set(t("status.saved", lang, files=', '.join(saved_list), folder=folder))
                self.root.after(0, _on_done)

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

    def _on_clear_params(self):
        """清除参数"""
        for entry in [self.entry_delta_0, self.entry_delta_01,
                      self.entry_delta_ret, self.entry_delta_02,
                      self.entry_h, self.entry_r0, self.entry_e,
                      self.entry_omega]:
            entry.delete(0, tk.END)
        self.status_var.set("")
        self.alpha_var.set("")

    def _on_clear_plots(self):
        """清除图像"""
        self._stop_animation()
        for ax in [self.ax_s, self.ax_v, self.ax_a,
                   self.ax_profile, self.ax_anim, self.ax_info]:
            ax.clear()
        self.canvas.draw()

    def _on_random(self):
        """随机凸轮参数"""
        params = generate_random_params()
        self._on_clear_params()

        self.entry_delta_0.insert(0, str(params['delta_0']))
        self.entry_delta_01.insert(0, str(params['delta_01']))
        self.entry_delta_ret.insert(0, str(params['delta_ret']))
        self.entry_delta_02.insert(0, str(params['delta_02']))
        self.entry_h.insert(0, str(params['h']))
        self.entry_r0.insert(0, str(params['r_0']))
        self.entry_e.insert(0, str(params['e']))
        self.entry_omega.insert(0, str(params['omega']))

        self.popup_tc.current(params['tc_law'] - 1)
        self.popup_hc.current(params['hc_law'] - 1)
        self.popup_sn.current(0 if params['sn'] == 1 else 1)
        self.popup_pz.current(0 if params['pz'] == 1 else 1)

    def _on_close(self):
        """窗口关闭处理"""
        self._stop_animation()
        self.root.destroy()

    def run(self):
        """运行主窗口"""
        self.root.mainloop()


if __name__ == '__main__':
    app = CamSimulator()
    app.run()
